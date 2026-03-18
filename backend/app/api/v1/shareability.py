"""Shareability API — manage shareability rules, compute index, trigger re-classification."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user_id, get_db
from app.llm.client import get_llm_client
from app.models.idea import Idea
from app.models.user import TenantMembership
from app.schemas.shareability import (
    ComponentShareabilityInfo,
    IdeaShareabilityResponse,
    ShareabilityRuleResponse,
    ShareabilityUpdate,
)
from app.services.shareability_service import ShareabilityService

router = APIRouter(tags=["shareability"])


async def _get_tenant_id(user_id: str, db: AsyncSession) -> uuid.UUID:
    membership = await db.scalar(
        select(TenantMembership).where(TenantMembership.user_id == uuid.UUID(user_id))
    )
    if not membership:
        raise HTTPException(status_code=400, detail="No tenant membership found")
    return membership.tenant_id


@router.get("/ideas/{idea_id}/shareability", response_model=IdeaShareabilityResponse)
async def get_idea_shareability(
    idea_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    idea = await db.scalar(
        select(Idea).where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    svc = ShareabilityService(db, get_llm_client())
    info = await svc.get_idea_shareability(idea_id, tenant_id)
    return IdeaShareabilityResponse(
        idea_id=info["idea_id"],
        shareability_index=info["shareability_index"],
        rules=[ShareabilityRuleResponse.model_validate(r) for r in info["rules"]],
        component_scores=[
            ComponentShareabilityInfo(**cs) for cs in info["component_scores"]
        ],
    )


@router.patch(
    "/ideas/{idea_id}/shareability", response_model=ShareabilityRuleResponse
)
async def update_idea_shareability(
    idea_id: uuid.UUID,
    data: ShareabilityUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    idea = await db.scalar(
        select(Idea).where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    svc = ShareabilityService(db, get_llm_client())
    rule = await svc.update_idea_shareability(
        idea_id, tenant_id, uuid.UUID(user_id), data.classification, data.min_access_tier
    )
    return ShareabilityRuleResponse.model_validate(rule)


@router.patch(
    "/components/{component_id}/shareability",
    response_model=ShareabilityRuleResponse,
)
async def update_component_shareability(
    component_id: uuid.UUID,
    data: ShareabilityUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    svc = ShareabilityService(db, get_llm_client())
    try:
        rule = await svc.update_component_shareability(
            component_id, tenant_id, uuid.UUID(user_id),
            data.classification, data.min_access_tier,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ShareabilityRuleResponse.model_validate(rule)


@router.post(
    "/ideas/{idea_id}/shareability/recompute",
    response_model=list[ShareabilityRuleResponse],
)
async def recompute_shareability(
    idea_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    idea = await db.scalar(
        select(Idea).where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    svc = ShareabilityService(db, get_llm_client())
    rules = await svc.recompute_all(idea_id, tenant_id)
    return [ShareabilityRuleResponse.model_validate(r) for r in rules]
