"""Consistency service — advisory checks for budget, deadlines, overlaps, cycles."""

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient
from app.models.consistency import ConsistencyFlag
from app.models.dependency import ComponentDependency
from app.models.idea import Idea, IdeaComponent
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

OVERLAP_THRESHOLD = 0.85  # Embedding similarity above this = component overlap


class ConsistencyService:
    def __init__(self, db: AsyncSession, llm_client: LLMClient):
        self.db = db
        self.embedding_svc = EmbeddingService(db, llm_client)
        self.llm_svc = LLMService(llm_client)

    async def run_all_checks(
        self, idea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[ConsistencyFlag]:
        """Run all consistency checks for an idea. Returns new flags created."""
        idea = await self.db.get(Idea, idea_id)
        if not idea:
            return []

        components = list(await self.db.scalars(
            select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
        ))

        # Clear existing unresolved flags for this idea
        existing = list(await self.db.scalars(
            select(ConsistencyFlag).where(
                ConsistencyFlag.idea_id == idea_id,
                ConsistencyFlag.resolved.is_(False),
                ConsistencyFlag.flag_type.notin_(
                    ["dependency_cycle", "dependency_deadline_conflict"]
                ),
            )
        ))
        for flag in existing:
            await self.db.delete(flag)

        flags: list[ConsistencyFlag] = []

        # Rule-based checks (fast, synchronous)
        flags.extend(self._check_budget(idea, components, tenant_id))
        flags.extend(self._check_deadlines(idea, components, tenant_id))

        # Embedding-based overlap check
        overlap_flags = await self._check_component_overlap(components, idea_id, tenant_id)
        flags.extend(overlap_flags)

        # LLM-based contradiction check (only if idea has description)
        if idea.description and len(components) >= 2:
            llm_flags = await self._check_llm_consistency(idea, components, tenant_id)
            flags.extend(llm_flags)

        for flag in flags:
            self.db.add(flag)

        await self.db.commit()
        return flags

    def _check_budget(
        self,
        idea: Idea,
        components: list[IdeaComponent],
        tenant_id: uuid.UUID,
    ) -> list[ConsistencyFlag]:
        """Check if sum of component costs exceeds idea total budget."""
        if not idea.total_budget:
            return []

        total_component_cost = sum(
            c.estimated_cost or Decimal(0) for c in components if c.estimated_cost
        )

        if total_component_cost > idea.total_budget:
            excess = total_component_cost - idea.total_budget
            return [
                ConsistencyFlag(
                    tenant_id=tenant_id,
                    idea_id=idea.id,
                    severity="warning",
                    flag_type="budget_exceeds_total",
                    description=(
                        f"Sum of component costs ({total_component_cost} {idea.budget_currency}) "
                        f"exceeds the idea's total budget ({idea.total_budget} {idea.budget_currency}) "
                        f"by {excess:.2f}."
                    ),
                )
            ]
        return []

    def _check_deadlines(
        self,
        idea: Idea,
        components: list[IdeaComponent],
        tenant_id: uuid.UUID,
    ) -> list[ConsistencyFlag]:
        """Check if any component deadlines are after the idea deadline."""
        if not idea.deadline:
            return []

        flags = []
        for comp in components:
            if comp.deadline and comp.deadline > idea.deadline:
                flags.append(
                    ConsistencyFlag(
                        tenant_id=tenant_id,
                        idea_id=idea.id,
                        component_id=comp.id,
                        severity="warning",
                        flag_type="deadline_conflict",
                        description=(
                            f"Component '{comp.name}' has a deadline ({comp.deadline.date()}) "
                            f"after the idea's overall deadline ({idea.deadline.date()})."
                        ),
                    )
                )
        return flags

    async def _check_component_overlap(
        self,
        components: list[IdeaComponent],
        idea_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[ConsistencyFlag]:
        """Find components within the same idea that describe similar work."""
        flags = []
        checked_pairs: set[frozenset] = set()

        for comp in components:
            if comp.embedding is None:
                continue

            similar = await self.embedding_svc.find_similar_components(
                embedding=comp.embedding,
                tenant_id=str(tenant_id),
                exclude_component_id=str(comp.id),
                threshold=OVERLAP_THRESHOLD,
            )

            for s in similar:
                if str(s["idea_id"]) != str(idea_id):
                    continue

                pair = frozenset([str(comp.id), str(s["id"])])
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)

                flags.append(
                    ConsistencyFlag(
                        tenant_id=tenant_id,
                        idea_id=idea_id,
                        component_id=comp.id,
                        severity="info",
                        flag_type="component_overlap",
                        description=(
                            f"Components '{comp.name}' and '{s['name']}' appear to describe "
                            f"similar work (similarity: {s['similarity']:.0%}). Consider merging."
                        ),
                    )
                )
        return flags

    async def _check_llm_consistency(
        self,
        idea: Idea,
        components: list[IdeaComponent],
        tenant_id: uuid.UUID,
    ) -> list[ConsistencyFlag]:
        """Use LLM to check for deeper consistency issues."""
        idea_dict = {
            "title": idea.title,
            "description": idea.description,
            "total_budget": float(idea.total_budget) if idea.total_budget else None,
            "budget_currency": idea.budget_currency,
            "deadline": idea.deadline.isoformat() if idea.deadline else None,
        }
        comp_dicts = [
            {
                "name": c.name,
                "description": c.description,
                "priority": c.priority,
                "status": c.status,
                "estimated_cost": float(c.estimated_cost) if c.estimated_cost else None,
                "deadline": c.deadline.isoformat() if c.deadline else None,
            }
            for c in components
        ]

        result = await self.llm_svc.check_consistency(idea_dict, comp_dicts)

        flags = []
        for issue in result.issues:
            flags.append(
                ConsistencyFlag(
                    tenant_id=tenant_id,
                    idea_id=idea.id,
                    severity=issue.severity,
                    flag_type=issue.flag_type,
                    description=issue.description,
                )
            )
        return flags

    async def get_idea_flags(
        self, idea_id: uuid.UUID, include_resolved: bool = False
    ) -> list[ConsistencyFlag]:
        """Get consistency flags for an idea."""
        query = select(ConsistencyFlag).where(ConsistencyFlag.idea_id == idea_id)
        if not include_resolved:
            query = query.where(ConsistencyFlag.resolved.is_(False))
        return list(await self.db.scalars(query))

    async def resolve_flag(
        self, flag_id: uuid.UUID, user_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> ConsistencyFlag:
        """Mark a flag as resolved."""
        flag = await self.db.scalar(
            select(ConsistencyFlag).where(
                ConsistencyFlag.id == flag_id,
                ConsistencyFlag.tenant_id == tenant_id,
            )
        )
        if not flag:
            raise ValueError("Flag not found")
        flag.resolved = True
        flag.resolved_by = user_id
        await self.db.commit()
        return flag
