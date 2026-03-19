"""Export service — serialize ideas to JSON, CSV, and Markdown."""

import csv
import io
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dependency import ComponentDependency
from app.models.idea import Idea, IdeaComponent
from app.models.link import IdeaLink


class ExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _load_idea(self, idea_id: uuid.UUID, tenant_id: uuid.UUID) -> Idea:
        idea = await self.db.scalar(
            select(Idea).where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
        )
        if not idea:
            raise ValueError("Idea not found")
        return idea

    async def _load_components(self, idea_id: uuid.UUID) -> list[IdeaComponent]:
        return list(
            await self.db.scalars(
                select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
            )
        )

    async def _load_dependencies(
        self, idea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[ComponentDependency]:
        comps = await self._load_components(idea_id)
        comp_ids = {c.id for c in comps}
        all_deps = list(
            await self.db.scalars(
                select(ComponentDependency).where(
                    ComponentDependency.tenant_id == tenant_id,
                    ComponentDependency.confirmed.is_(True),
                )
            )
        )
        return [
            d for d in all_deps
            if d.source_component_id in comp_ids or d.target_component_id in comp_ids
        ]

    async def _load_links(
        self, idea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[IdeaLink]:
        return list(
            await self.db.scalars(
                select(IdeaLink).where(
                    IdeaLink.tenant_id == tenant_id,
                    IdeaLink.confirmed.is_(True),
                    (IdeaLink.source_idea_id == idea_id)
                    | (IdeaLink.target_idea_id == idea_id),
                )
            )
        )

    async def export_idea_json(
        self, idea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> dict:
        idea = await self._load_idea(idea_id, tenant_id)
        components = await self._load_components(idea_id)
        deps = await self._load_dependencies(idea_id, tenant_id)
        links = await self._load_links(idea_id, tenant_id)

        comp_map: dict[uuid.UUID, str] = {c.id: c.name for c in components}

        return {
            "id": str(idea.id),
            "title": idea.title,
            "description": idea.description,
            "status": idea.status,
            "version": idea.version,
            "deadline": idea.deadline.isoformat() if idea.deadline else None,
            "total_budget": float(idea.total_budget) if idea.total_budget else None,
            "budget_currency": idea.budget_currency,
            "created_at": idea.created_at.isoformat(),
            "updated_at": idea.updated_at.isoformat(),
            "components": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "description": c.description,
                    "priority": c.priority,
                    "status": c.status,
                    "estimated_cost": float(c.estimated_cost) if c.estimated_cost else None,
                    "deadline": c.deadline.isoformat() if c.deadline else None,
                    "shareability_score": float(c.shareability_score),
                }
                for c in components
            ],
            "dependencies": [
                {
                    "id": str(d.id),
                    "source_component": comp_map.get(d.source_component_id, str(d.source_component_id)),
                    "target_component": comp_map.get(d.target_component_id, str(d.target_component_id)),
                    "dependency_type": d.dependency_type,
                    "is_cross_idea": d.is_cross_idea,
                }
                for d in deps
            ],
            "links": [
                {
                    "id": str(link.id),
                    "source_idea_id": str(link.source_idea_id),
                    "target_idea_id": str(link.target_idea_id),
                    "link_type": link.link_type,
                    "similarity_score": link.similarity_score,
                    "rationale": link.llm_rationale,
                }
                for link in links
            ],
        }

    async def export_idea_csv(
        self, idea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> str:
        idea = await self._load_idea(idea_id, tenant_id)
        components = await self._load_components(idea_id)
        deps = await self._load_dependencies(idea_id, tenant_id)

        output = io.StringIO()
        writer = csv.writer(output)

        # Idea header
        writer.writerow(["IDEA"])
        writer.writerow(["ID", "Title", "Status", "Version", "Deadline", "Total Budget", "Currency"])
        writer.writerow([
            str(idea.id), idea.title, idea.status, idea.version,
            idea.deadline.date() if idea.deadline else "",
            float(idea.total_budget) if idea.total_budget else "",
            idea.budget_currency,
        ])
        writer.writerow([])

        # Components
        writer.writerow(["COMPONENTS"])
        writer.writerow(["ID", "Name", "Priority", "Status", "Estimated Cost", "Deadline", "Shareability Score"])
        for c in components:
            writer.writerow([
                str(c.id), c.name, c.priority, c.status,
                float(c.estimated_cost) if c.estimated_cost else "",
                c.deadline.date() if c.deadline else "",
                float(c.shareability_score),
            ])
        writer.writerow([])

        # Dependencies
        comp_map: dict[uuid.UUID, str] = {c.id: c.name for c in components}
        writer.writerow(["DEPENDENCIES"])
        writer.writerow(["Source Component", "Target Component", "Type", "Cross-Idea"])
        for d in deps:
            writer.writerow([
                comp_map.get(d.source_component_id, str(d.source_component_id)),
                comp_map.get(d.target_component_id, str(d.target_component_id)),
                d.dependency_type,
                d.is_cross_idea,
            ])

        return output.getvalue()

    async def export_idea_markdown(
        self, idea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> str:
        idea = await self._load_idea(idea_id, tenant_id)
        components = await self._load_components(idea_id)
        deps = await self._load_dependencies(idea_id, tenant_id)
        links = await self._load_links(idea_id, tenant_id)

        comp_map: dict[uuid.UUID, str] = {c.id: c.name for c in components}

        lines: list[str] = []

        # Header
        lines.append(f"# {idea.title}")
        lines.append("")
        lines.append(idea.description or "")
        lines.append("")

        # Meta
        meta = []
        if idea.deadline:
            meta.append(f"- **Deadline:** {idea.deadline.date()}")
        if idea.total_budget:
            meta.append(f"- **Budget:** {float(idea.total_budget):,.2f} {idea.budget_currency}")
        meta.append(f"- **Status:** {idea.status}")
        meta.append(f"- **Version:** v{idea.version}")
        if meta:
            lines.extend(meta)
            lines.append("")

        # Components
        lines.append("## Components")
        lines.append("")
        if components:
            lines.append("| Name | Priority | Status | Cost | Deadline |")
            lines.append("|------|----------|--------|------|----------|")
            for c in components:
                cost = f"{float(c.estimated_cost):,.2f}" if c.estimated_cost else "—"
                deadline = str(c.deadline.date()) if c.deadline else "—"
                lines.append(
                    f"| {c.name} | {c.priority.replace('_', ' ')} "
                    f"| {c.status.replace('_', ' ')} | {cost} | {deadline} |"
                )
        else:
            lines.append("_No components._")
        lines.append("")

        # Dependencies
        lines.append("## Dependencies")
        lines.append("")
        if deps:
            for d in deps:
                src = comp_map.get(d.source_component_id, str(d.source_component_id))
                tgt = comp_map.get(d.target_component_id, str(d.target_component_id))
                cross = " _(cross-idea)_" if d.is_cross_idea else ""
                lines.append(f"- **{src}** → **{tgt}** `{d.dependency_type}`{cross}")
        else:
            lines.append("_No dependencies._")
        lines.append("")

        # Cross-idea links
        if links:
            lines.append("## Cross-Idea Links")
            lines.append("")
            for link in links:
                other = (
                    str(link.target_idea_id)
                    if link.source_idea_id == idea_id
                    else str(link.source_idea_id)
                )
                lines.append(
                    f"- `{link.link_type}` with idea `{other}` "
                    f"(similarity: {link.similarity_score:.2f})"
                )
                if link.llm_rationale:
                    lines.append(f"  > {link.llm_rationale}")
            lines.append("")

        return "\n".join(lines)
