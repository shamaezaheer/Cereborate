"""Shareability service — classification, index computation, cross-idea auto-exposure."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient
from app.models.dependency import ComponentDependency
from app.models.idea import Idea, IdeaComponent
from app.models.shareability import AccessGrant, ShareabilityRule
from app.services.llm_service import LLMService


# Classification → tier mapping
CLASSIFICATION_TIERS = {
    "public": 1,
    "internal": 3,
    "confidential": 5,
    "restricted": 7,
}


class ShareabilityService:
    def __init__(self, db: AsyncSession, llm_client: LLMClient):
        self.db = db
        self.llm_svc = LLMService(llm_client)

    async def classify_component(
        self, component_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> ShareabilityRule:
        """Use LLM to classify a component's shareability and create/update the rule."""
        component = await self.db.get(IdeaComponent, component_id)
        if not component:
            raise ValueError("Component not found")

        idea = await self.db.get(Idea, component.idea_id)
        if not idea:
            raise ValueError("Idea not found")

        result = await self.llm_svc.score_shareability(
            component={
                "name": component.name,
                "description": component.description,
                "priority": component.priority,
                "estimated_cost": float(component.estimated_cost) if component.estimated_cost else None,
            },
            idea_context=f"{idea.title}: {idea.description}",
        )

        # Update component's inline score
        component.shareability_score = result.score
        component.shareability_reason = result.rationale

        # Find or create rule
        existing = await self.db.scalar(
            select(ShareabilityRule).where(
                ShareabilityRule.component_id == component_id,
                ShareabilityRule.tenant_id == tenant_id,
            )
        )

        if existing and not existing.overridden_by:
            existing.classification = result.classification
            existing.min_access_tier = result.min_access_tier
            existing.auto_classified = True
            rule = existing
        elif not existing:
            rule = ShareabilityRule(
                tenant_id=tenant_id,
                idea_id=component.idea_id,
                component_id=component_id,
                min_access_tier=result.min_access_tier,
                classification=result.classification,
                auto_classified=True,
            )
            self.db.add(rule)

        else:
            rule = existing

        await self.db.commit()
        return rule

    async def compute_shareability_index(self, idea_id: uuid.UUID) -> float:
        """Compute weighted average shareability index for an idea."""
        components = list(
            await self.db.scalars(
                select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
            )
        )

        if not components:
            return 0.5

        # Weight by priority
        priority_weights = {
            "must_have": 3.0,
            "should_have": 2.0,
            "nice_to_have": 1.0,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for comp in components:
            weight = priority_weights.get(comp.priority, 1.0)
            if comp.estimated_cost and comp.estimated_cost > 0:
                weight *= 1.5  # Budget-weighted
            weighted_sum += float(comp.shareability_score) * weight
            total_weight += weight

        if total_weight == 0:
            return 0.5

        return round(weighted_sum / total_weight, 4)

    async def get_idea_shareability(
        self, idea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> dict:
        """Get full shareability info for an idea."""
        index = await self.compute_shareability_index(idea_id)

        rules = list(
            await self.db.scalars(
                select(ShareabilityRule).where(
                    ShareabilityRule.tenant_id == tenant_id,
                    ShareabilityRule.idea_id == idea_id,
                )
            )
        )

        components = list(
            await self.db.scalars(
                select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
            )
        )

        # Build per-component info
        rule_by_comp = {r.component_id: r for r in rules if r.component_id}
        component_scores = []
        for comp in components:
            rule = rule_by_comp.get(comp.id)
            component_scores.append({
                "component_id": comp.id,
                "name": comp.name,
                "shareability_score": float(comp.shareability_score),
                "classification": rule.classification if rule else "public",
                "min_access_tier": rule.min_access_tier if rule else 1,
                "auto_classified": rule.auto_classified if rule else False,
            })

        return {
            "idea_id": idea_id,
            "shareability_index": index,
            "rules": rules,
            "component_scores": component_scores,
        }

    async def update_component_shareability(
        self,
        component_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        classification: str,
        min_access_tier: int,
    ) -> ShareabilityRule:
        """Override a component's shareability (manual user action)."""
        component = await self.db.get(IdeaComponent, component_id)
        if not component:
            raise ValueError("Component not found")

        existing = await self.db.scalar(
            select(ShareabilityRule).where(
                ShareabilityRule.component_id == component_id,
                ShareabilityRule.tenant_id == tenant_id,
            )
        )

        if existing:
            existing.classification = classification
            existing.min_access_tier = min_access_tier
            existing.auto_classified = False
            existing.overridden_by = user_id
            rule = existing
        else:
            rule = ShareabilityRule(
                tenant_id=tenant_id,
                idea_id=component.idea_id,
                component_id=component_id,
                min_access_tier=min_access_tier,
                classification=classification,
                auto_classified=False,
                overridden_by=user_id,
            )
            self.db.add(rule)

        await self.db.commit()
        return rule

    async def update_idea_shareability(
        self,
        idea_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        classification: str,
        min_access_tier: int,
    ) -> ShareabilityRule:
        """Set/update idea-level shareability rule."""
        existing = await self.db.scalar(
            select(ShareabilityRule).where(
                ShareabilityRule.idea_id == idea_id,
                ShareabilityRule.component_id.is_(None),
                ShareabilityRule.tenant_id == tenant_id,
            )
        )

        if existing:
            existing.classification = classification
            existing.min_access_tier = min_access_tier
            existing.auto_classified = False
            existing.overridden_by = user_id
            rule = existing
        else:
            rule = ShareabilityRule(
                tenant_id=tenant_id,
                idea_id=idea_id,
                component_id=None,
                min_access_tier=min_access_tier,
                classification=classification,
                auto_classified=False,
                overridden_by=user_id,
            )
            self.db.add(rule)

        await self.db.commit()
        return rule

    async def auto_expose_cross_idea_dep(
        self, dep_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> None:
        """When a cross-idea dependency is confirmed, lower both components'
        effective shareability to the less restrictive of the two,
        so both teams can see the shared surface."""
        dep = await self.db.scalar(
            select(ComponentDependency).where(
                ComponentDependency.id == dep_id,
                ComponentDependency.tenant_id == tenant_id,
                ComponentDependency.is_cross_idea.is_(True),
            )
        )
        if not dep or not dep.confirmed:
            return

        source_rule = await self.db.scalar(
            select(ShareabilityRule).where(
                ShareabilityRule.component_id == dep.source_component_id,
                ShareabilityRule.tenant_id == tenant_id,
            )
        )
        target_rule = await self.db.scalar(
            select(ShareabilityRule).where(
                ShareabilityRule.component_id == dep.target_component_id,
                ShareabilityRule.tenant_id == tenant_id,
            )
        )

        source_tier = source_rule.min_access_tier if source_rule else 1
        target_tier = target_rule.min_access_tier if target_rule else 1
        min_tier = min(source_tier, target_tier)

        # Lower both to the less restrictive tier
        source_comp = await self.db.get(IdeaComponent, dep.source_component_id)
        target_comp = await self.db.get(IdeaComponent, dep.target_component_id)

        for comp, rule in [(source_comp, source_rule), (target_comp, target_rule)]:
            if not comp:
                continue
            if rule:
                if rule.min_access_tier > min_tier and not rule.overridden_by:
                    rule.min_access_tier = min_tier
            else:
                new_rule = ShareabilityRule(
                    tenant_id=tenant_id,
                    idea_id=comp.idea_id,
                    component_id=comp.id,
                    min_access_tier=min_tier,
                    classification="internal" if min_tier <= 4 else "public",
                    auto_classified=True,
                )
                self.db.add(new_rule)

        await self.db.commit()

    async def recompute_all(
        self, idea_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[ShareabilityRule]:
        """Trigger re-classification of all components in an idea."""
        components = list(
            await self.db.scalars(
                select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
            )
        )
        rules = []
        for comp in components:
            rule = await self.classify_component(comp.id, tenant_id)
            rules.append(rule)
        return rules
