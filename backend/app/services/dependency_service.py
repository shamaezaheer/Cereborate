"""Dependency service — manages component dependency DAG with cycle detection."""

import uuid
from collections import defaultdict, deque
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient
from app.models.consistency import ConsistencyFlag
from app.models.dependency import ComponentDependency
from app.models.idea import Idea, IdeaComponent
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService


DEPENDENCY_TYPES = {"blocks", "requires_output", "shares_resource", "extends", "informed_by"}


class DependencyService:
    def __init__(self, db: AsyncSession, llm_client: LLMClient):
        self.db = db
        self.embedding_svc = EmbeddingService(db, llm_client)
        self.llm_svc = LLMService(llm_client)

    async def add_dependency(
        self,
        source_component_id: uuid.UUID,
        target_component_id: uuid.UUID,
        dependency_type: str,
        tenant_id: uuid.UUID,
        llm_detected: bool = False,
        llm_rationale: str | None = None,
    ) -> tuple[ComponentDependency, list[ConsistencyFlag]]:
        """Add a dependency and return it along with any consistency flags raised."""
        if dependency_type not in DEPENDENCY_TYPES:
            raise ValueError(f"Invalid dependency type: {dependency_type}")

        source = await self.db.get(IdeaComponent, source_component_id)
        target = await self.db.get(IdeaComponent, target_component_id)

        if not source or not target:
            raise ValueError("Component not found")

        is_cross_idea = source.idea_id != target.idea_id

        # Check for cycles before adding
        would_cycle = await self._would_create_cycle(
            source_component_id, target_component_id, tenant_id
        )

        dep = ComponentDependency(
            tenant_id=tenant_id,
            source_component_id=source_component_id,
            target_component_id=target_component_id,
            dependency_type=dependency_type,
            is_cross_idea=is_cross_idea,
            llm_detected=llm_detected,
            confirmed=not llm_detected,
            llm_rationale=llm_rationale,
        )
        self.db.add(dep)
        await self.db.flush()

        flags = []

        # Flag cycle
        if would_cycle:
            flag = ConsistencyFlag(
                tenant_id=tenant_id,
                idea_id=source.idea_id,
                component_id=source_component_id,
                severity="critical",
                flag_type="dependency_cycle",
                description=(
                    f"Adding dependency from '{source.name}' to '{target.name}' "
                    f"creates a circular dependency chain."
                ),
            )
            self.db.add(flag)
            flags.append(flag)

        # Check deadline conflict (blocks dependency only)
        if dependency_type == "blocks":
            flag = await self._check_deadline_conflict(source, target, tenant_id)
            if flag:
                self.db.add(flag)
                flags.append(flag)

        await self.db.commit()
        return dep, flags

    async def _would_create_cycle(
        self,
        new_source: uuid.UUID,
        new_target: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> bool:
        """Check if adding source→target would create a cycle using BFS/DFS."""
        # Load all existing edges in tenant
        edges = await self.db.scalars(
            select(ComponentDependency).where(ComponentDependency.tenant_id == tenant_id)
        )
        adj: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
        for e in edges:
            adj[e.source_component_id].append(e.target_component_id)

        # Add the proposed edge
        adj[new_source].append(new_target)

        # DFS from new_target to see if we can reach new_source
        visited: set[uuid.UUID] = set()
        stack = deque([new_target])
        while stack:
            node = stack.popleft()
            if node == new_source:
                return True
            if node in visited:
                continue
            visited.add(node)
            stack.extend(adj[node])
        return False

    async def _check_deadline_conflict(
        self,
        source: IdeaComponent,
        target: IdeaComponent,
        tenant_id: uuid.UUID,
    ) -> ConsistencyFlag | None:
        """A 'blocks' dep means target must finish before source starts."""
        if not source.deadline or not target.deadline:
            return None
        if target.deadline >= source.deadline:
            return ConsistencyFlag(
                tenant_id=tenant_id,
                idea_id=source.idea_id,
                component_id=source.id,
                severity="warning",
                flag_type="dependency_deadline_conflict",
                description=(
                    f"'{target.name}' (deadline {target.deadline.date()}) blocks "
                    f"'{source.name}' (deadline {source.deadline.date()}), but the "
                    f"blocker's deadline is after the dependent's deadline."
                ),
            )
        return None

    async def get_dependency_graph(
        self, idea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> dict:
        """Return the full DAG for an idea as nodes + edges."""
        components = await self.db.scalars(
            select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
        )
        comp_ids = {c.id for c in components}

        # Get all deps where source or target is in this idea
        all_deps = await self.db.scalars(
            select(ComponentDependency).where(ComponentDependency.tenant_id == tenant_id)
        )
        deps = [
            d for d in all_deps
            if d.source_component_id in comp_ids or d.target_component_id in comp_ids
        ]

        nodes = []
        for cid in comp_ids:
            comp = await self.db.get(IdeaComponent, cid)
            if comp:
                nodes.append({
                    "id": str(comp.id),
                    "name": comp.name,
                    "status": comp.status,
                    "priority": comp.priority,
                })

        edges = [
            {
                "id": str(d.id),
                "source": str(d.source_component_id),
                "target": str(d.target_component_id),
                "type": d.dependency_type,
                "is_cross_idea": d.is_cross_idea,
                "confirmed": d.confirmed,
            }
            for d in deps
        ]

        return {"nodes": nodes, "edges": edges}

    async def confirm_dependency(
        self, dep_id: uuid.UUID, confirmed: bool, tenant_id: uuid.UUID
    ) -> ComponentDependency:
        """Confirm or reject an LLM-detected dependency."""
        dep = await self.db.scalar(
            select(ComponentDependency).where(
                ComponentDependency.id == dep_id,
                ComponentDependency.tenant_id == tenant_id,
            )
        )
        if not dep:
            raise ValueError("Dependency not found")
        dep.confirmed = confirmed
        await self.db.commit()
        return dep

    async def detect_cross_idea_dependencies(
        self, idea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[ComponentDependency]:
        """Use embeddings + LLM to detect potential cross-idea dependencies."""
        components = list(await self.db.scalars(
            select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
        ))

        detected = []
        for comp in components:
            if comp.embedding is None:
                continue

            similar_comps = await self.embedding_svc.find_similar_components(
                embedding=comp.embedding,
                tenant_id=str(tenant_id),
                exclude_component_id=str(comp.id),
                threshold=0.75,
            )

            for similar in similar_comps:
                # Only consider cross-idea components
                if str(similar["idea_id"]) == str(idea_id):
                    continue

                result = await self.llm_svc.detect_dependency(
                    comp_a={"name": comp.name, "description": comp.description, "idea_title": ""},
                    comp_b={
                        "name": similar["name"],
                        "description": similar["description"],
                        "idea_title": similar["idea_title"],
                    },
                    similarity_score=float(similar["similarity"]),
                )

                if result.has_dependency and result.confidence >= 0.65:
                    dep, _ = await self.add_dependency(
                        source_component_id=comp.id,
                        target_component_id=uuid.UUID(str(similar["id"])),
                        dependency_type=result.dependency_type or "informed_by",
                        tenant_id=tenant_id,
                        llm_detected=True,
                        llm_rationale=result.rationale,
                    )
                    detected.append(dep)

        return detected

    async def get_shared_dependencies(
        self, tenant_id: uuid.UUID, user_idea_ids: list[uuid.UUID]
    ) -> list[dict]:
        """Get cross-idea dependencies visible to the user (their ideas are involved)."""
        if not user_idea_ids:
            return []

        # Get all components from user's ideas
        user_components = list(await self.db.scalars(
            select(IdeaComponent).where(
                IdeaComponent.idea_id.in_(user_idea_ids)
            )
        ))
        user_comp_ids = {c.id for c in user_components}

        # Get cross-idea deps where one side belongs to user
        all_cross_deps = list(await self.db.scalars(
            select(ComponentDependency).where(
                ComponentDependency.tenant_id == tenant_id,
                ComponentDependency.is_cross_idea.is_(True),
                ComponentDependency.confirmed.is_(True),
            )
        ))

        relevant = [
            d for d in all_cross_deps
            if d.source_component_id in user_comp_ids
            or d.target_component_id in user_comp_ids
        ]

        result = []
        for dep in relevant:
            source = await self.db.get(IdeaComponent, dep.source_component_id)
            target = await self.db.get(IdeaComponent, dep.target_component_id)
            if source and target:
                result.append({
                    "dependency_id": str(dep.id),
                    "dependency_type": dep.dependency_type,
                    "source": {
                        "id": str(source.id),
                        "name": source.name,
                        "description": source.description,
                        "status": source.status,
                        "deadline": source.deadline.isoformat() if source.deadline else None,
                        "idea_id": str(source.idea_id),
                    },
                    "target": {
                        "id": str(target.id),
                        "name": target.name,
                        "description": target.description,
                        "status": target.status,
                        "deadline": target.deadline.isoformat() if target.deadline else None,
                        "idea_id": str(target.idea_id),
                    },
                })
        return result
