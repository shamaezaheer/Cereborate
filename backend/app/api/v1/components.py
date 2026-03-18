import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user_id, get_db
from app.models.idea import Idea, IdeaComponent
from app.models.user import TenantMembership
from app.schemas.idea import ComponentCreate, ComponentResponse, ComponentUpdate

router = APIRouter(tags=["components"])


async def _get_tenant_id(user_id: str, db: AsyncSession) -> uuid.UUID:
    membership = await db.scalar(
        select(TenantMembership).where(TenantMembership.user_id == uuid.UUID(user_id))
    )
    if not membership:
        raise HTTPException(status_code=400, detail="No tenant membership found")
    return membership.tenant_id


@router.get("/ideas/{idea_id}/components", response_model=list[ComponentResponse])
async def list_components(
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

    components = await db.scalars(
        select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
    )
    return [ComponentResponse.model_validate(c) for c in components]


@router.post("/ideas/{idea_id}/components", response_model=ComponentResponse, status_code=201)
async def create_component(
    idea_id: uuid.UUID,
    data: ComponentCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    idea = await db.scalar(
        select(Idea).where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    component = IdeaComponent(
        tenant_id=tenant_id,
        idea_id=idea_id,
        name=data.name,
        description=data.description,
        priority=data.priority,
        estimated_cost=data.estimated_cost,
        deadline=data.deadline,
    )
    db.add(component)
    await db.commit()
    await db.refresh(component)
    return ComponentResponse.model_validate(component)


@router.patch("/components/{component_id}", response_model=ComponentResponse)
async def update_component(
    component_id: uuid.UUID,
    data: ComponentUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    component = await db.scalar(
        select(IdeaComponent).where(
            IdeaComponent.id == component_id, IdeaComponent.tenant_id == tenant_id
        )
    )
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(component, key, value)

    await db.commit()
    await db.refresh(component)
    return ComponentResponse.model_validate(component)


@router.delete("/components/{component_id}", status_code=204)
async def delete_component(
    component_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    component = await db.scalar(
        select(IdeaComponent).where(
            IdeaComponent.id == component_id, IdeaComponent.tenant_id == tenant_id
        )
    )
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    await db.delete(component)
    await db.commit()
