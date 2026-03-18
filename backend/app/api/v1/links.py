import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user_id, get_db
from app.llm.client import get_llm_client
from app.models.idea import Idea
from app.models.link import IdeaLink
from app.models.user import TenantMembership
from app.services.linking_service import LinkingService

router = APIRouter(tags=["links"])


class LinkResponse(BaseModel):
    id: uuid.UUID
    source_idea_id: uuid.UUID
    target_idea_id: uuid.UUID
    link_type: str
    similarity_score: float
    llm_rationale: str | None
    confirmed: bool

    model_config = {"from_attributes": True}


async def _get_tenant_id(user_id: str, db: AsyncSession) -> uuid.UUID:
    membership = await db.scalar(
        select(TenantMembership).where(TenantMembership.user_id == uuid.UUID(user_id))
    )
    if not membership:
        raise HTTPException(status_code=400, detail="No tenant membership found")
    return membership.tenant_id


@router.get("/ideas/{idea_id}/links", response_model=list[LinkResponse])
async def get_idea_links(
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

    svc = LinkingService(db, get_llm_client())
    links = await svc.get_idea_links(idea_id)
    return [LinkResponse.model_validate(l) for l in links]
