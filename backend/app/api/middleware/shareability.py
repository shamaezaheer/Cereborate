"""Shareability access filtering middleware for team-facing queries."""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.shareability import AccessGrant, ShareabilityRule


def filter_ideas_by_access(
    query: Select,
    user_id: uuid.UUID,
    user_tier: int,
    tenant_id: uuid.UUID,
    idea_id_column,
) -> Select:
    """Filter a query to only include ideas the user has access to based on tier.

    Applies shareability rules: ideas with no rule default to public (visible).
    Ideas with a rule require user_tier >= min_access_tier, or an explicit grant.
    """
    # Sub-select for idea-level rules
    rule_subq = (
        select(ShareabilityRule.idea_id)
        .where(
            ShareabilityRule.tenant_id == tenant_id,
            ShareabilityRule.component_id.is_(None),
            ShareabilityRule.min_access_tier > user_tier,
        )
        .correlate_except(ShareabilityRule)
    )

    # Sub-select for explicit grants
    grant_subq = (
        select(AccessGrant.idea_id)
        .where(
            AccessGrant.tenant_id == tenant_id,
            AccessGrant.granted_to_user_id == user_id,
        )
        .correlate_except(AccessGrant)
    )

    return query.where(
        or_(
            idea_id_column.not_in(rule_subq),  # No restrictive rule
            idea_id_column.in_(grant_subq),  # Explicit grant
        )
    )


def filter_components_by_access(
    query: Select,
    user_id: uuid.UUID,
    user_tier: int,
    tenant_id: uuid.UUID,
    component_id_column,
) -> Select:
    """Filter components by user's access tier and explicit grants."""
    rule_subq = (
        select(ShareabilityRule.component_id)
        .where(
            ShareabilityRule.tenant_id == tenant_id,
            ShareabilityRule.component_id.is_not(None),
            ShareabilityRule.min_access_tier > user_tier,
        )
        .correlate_except(ShareabilityRule)
    )

    grant_subq = (
        select(AccessGrant.component_id)
        .where(
            AccessGrant.tenant_id == tenant_id,
            AccessGrant.granted_to_user_id == user_id,
            AccessGrant.component_id.is_not(None),
        )
        .correlate_except(AccessGrant)
    )

    return query.where(
        or_(
            component_id_column.not_in(rule_subq),
            component_id_column.in_(grant_subq),
        )
    )


async def get_user_access_tier(
    db: AsyncSession, user_id: uuid.UUID, tenant_id: uuid.UUID
) -> int:
    """Get user's access tier from their tenant membership."""
    from app.models.user import TenantMembership

    membership = await db.scalar(
        select(TenantMembership).where(
            TenantMembership.user_id == user_id,
            TenantMembership.tenant_id == tenant_id,
        )
    )
    if not membership:
        return 0
    return membership.access_tier
