import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user_id, get_db
from app.llm.client import get_llm_client
from app.models.consistency import ConsistencyFlag
from app.models.idea import Idea
from app.models.user import TenantMembership
from app.services.consistency_service import ConsistencyService

router = APIRouter(tags=["consistency"])


class FlagResponse(BaseModel):
    id: uuid.UUID
    severity: str
    flag_type: str
    description: str
    component_id: uuid.UUID | None
    resolved: bool

    model_config = {"from_attributes": True}


class FlagResolveRequest(BaseModel):
    resolved: bool = True


async def _get_tenant_id(user_id: str, db: AsyncSession) -> uuid.UUID:
    membership = await db.scalar(
        select(TenantMembership).where(TenantMembership.user_id == uuid.UUID(user_id))
    )
    if not membership:
        raise HTTPException(status_code=400, detail="No tenant membership found")
    return membership.tenant_id


@router.get("/ideas/{idea_id}/consistency", response_model=list[FlagResponse])
async def get_consistency_flags(
    idea_id: uuid.UUID,
    include_resolved: bool = False,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    idea = await db.scalar(
        select(Idea).where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    svc = ConsistencyService(db, get_llm_client())
    flags = await svc.get_idea_flags(idea_id, include_resolved)
    return [FlagResponse.model_validate(f) for f in flags]


@router.post("/ideas/{idea_id}/consistency/check", response_model=list[FlagResponse])
async def trigger_consistency_check(
    idea_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a full consistency check for an idea."""
    tenant_id = await _get_tenant_id(user_id, db)
    idea = await db.scalar(
        select(Idea).where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    svc = ConsistencyService(db, get_llm_client())
    flags = await svc.run_all_checks(idea_id, tenant_id)
    return [FlagResponse.model_validate(f) for f in flags]


@router.patch("/consistency/{flag_id}/resolve", response_model=FlagResponse)
async def resolve_flag(
    flag_id: uuid.UUID,
    data: FlagResolveRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    svc = ConsistencyService(db, get_llm_client())
    try:
        flag = await svc.resolve_flag(flag_id, uuid.UUID(user_id), tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FlagResponse.model_validate(flag)
