import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_current_user_id, get_db
from app.models.idea import Idea, IdeaStatus, IdeaVersion
from app.models.user import TenantMembership
from app.schemas.idea import IdeaCreate, IdeaDetailResponse, IdeaResponse, IdeaUpdate

router = APIRouter(prefix="/ideas", tags=["ideas"])


async def _get_tenant_id(user_id: str, db: AsyncSession) -> uuid.UUID:
    membership = await db.scalar(
        select(TenantMembership).where(TenantMembership.user_id == uuid.UUID(user_id))
    )
    if not membership:
        raise HTTPException(status_code=400, detail="No tenant membership found")
    return membership.tenant_id


async def _get_idea_or_404(
    idea_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession
) -> Idea:
    idea = await db.scalar(
        select(Idea)
        .where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
        .options(selectinload(Idea.components))
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return idea


@router.get("", response_model=list[IdeaResponse])
async def list_ideas(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    ideas = await db.scalars(
        select(Idea).where(
            Idea.tenant_id == tenant_id,
            Idea.creator_id == uuid.UUID(user_id),
            Idea.status != IdeaStatus.archived,
        )
    )
    return [IdeaResponse.model_validate(i) for i in ideas]


@router.post("", response_model=IdeaResponse, status_code=201)
async def create_idea(
    data: IdeaCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    idea = Idea(
        tenant_id=tenant_id,
        creator_id=uuid.UUID(user_id),
        title=data.title,
        description=data.description,
        deadline=data.deadline,
        total_budget=data.total_budget,
        budget_currency=data.budget_currency,
        version=1,
    )
    db.add(idea)
    await db.flush()

    version = IdeaVersion(
        tenant_id=tenant_id,
        idea_id=idea.id,
        version=1,
        snapshot={"title": idea.title, "description": idea.description},
        changed_by=uuid.UUID(user_id),
        created_at=datetime.now(timezone.utc),
    )
    db.add(version)
    await db.commit()
    await db.refresh(idea)
    return IdeaResponse.model_validate(idea)


@router.get("/{idea_id}", response_model=IdeaDetailResponse)
async def get_idea(
    idea_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    idea = await _get_idea_or_404(idea_id, tenant_id, db)
    return IdeaDetailResponse.model_validate(idea)


@router.patch("/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: uuid.UUID,
    data: IdeaUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    idea = await _get_idea_or_404(idea_id, tenant_id, db)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(idea, key, value)

    idea.version += 1
    version = IdeaVersion(
        tenant_id=tenant_id,
        idea_id=idea.id,
        version=idea.version,
        snapshot={"title": idea.title, "description": idea.description},
        changed_by=uuid.UUID(user_id),
        created_at=datetime.now(timezone.utc),
    )
    db.add(version)
    await db.commit()
    await db.refresh(idea)
    return IdeaResponse.model_validate(idea)


@router.delete("/{idea_id}", status_code=204)
async def archive_idea(
    idea_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    idea = await _get_idea_or_404(idea_id, tenant_id, db)
    idea.status = IdeaStatus.archived
    await db.commit()
