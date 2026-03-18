import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user_id, get_db
from app.llm.client import get_llm_client
from app.models.dependency import ComponentDependency
from app.models.idea import Idea, IdeaComponent
from app.models.user import TenantMembership
from app.schemas.dependency import (
    DependencyConfirmRequest,
    DependencyCreate,
    DependencyGraphResponse,
    DependencyResponse,
    SharedDependencyResponse,
)
from app.services.dependency_service import DependencyService

router = APIRouter(tags=["dependencies"])


async def _get_tenant_id(user_id: str, db: AsyncSession) -> uuid.UUID:
    membership = await db.scalar(
        select(TenantMembership).where(TenantMembership.user_id == uuid.UUID(user_id))
    )
    if not membership:
        raise HTTPException(status_code=400, detail="No tenant membership found")
    return membership.tenant_id


@router.get("/ideas/{idea_id}/dependencies", response_model=list[DependencyResponse])
async def list_idea_dependencies(
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

    components = list(await db.scalars(
        select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
    ))
    comp_ids = {c.id for c in components}

    deps = list(await db.scalars(
        select(ComponentDependency).where(
            ComponentDependency.tenant_id == tenant_id,
            (ComponentDependency.source_component_id.in_(comp_ids))
            | (ComponentDependency.target_component_id.in_(comp_ids)),
        )
    ))
    return [DependencyResponse.model_validate(d) for d in deps]


@router.post(
    "/components/{component_id}/dependencies",
    response_model=DependencyResponse,
    status_code=201,
)
async def add_dependency(
    component_id: uuid.UUID,
    data: DependencyCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    svc = DependencyService(db, get_llm_client())
    try:
        dep, flags = await svc.add_dependency(
            source_component_id=component_id,
            target_component_id=data.target_component_id,
            dependency_type=data.dependency_type,
            tenant_id=tenant_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DependencyResponse.model_validate(dep)


@router.delete("/dependencies/{dep_id}", status_code=204)
async def remove_dependency(
    dep_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    dep = await db.scalar(
        select(ComponentDependency).where(
            ComponentDependency.id == dep_id, ComponentDependency.tenant_id == tenant_id
        )
    )
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")
    await db.delete(dep)
    await db.commit()


@router.patch("/dependencies/{dep_id}/confirm", response_model=DependencyResponse)
async def confirm_dependency(
    dep_id: uuid.UUID,
    data: DependencyConfirmRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    svc = DependencyService(db, get_llm_client())
    try:
        dep = await svc.confirm_dependency(dep_id, data.confirmed, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return DependencyResponse.model_validate(dep)


@router.get("/ideas/{idea_id}/dependency-graph", response_model=DependencyGraphResponse)
async def get_dependency_graph(
    idea_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    svc = DependencyService(db, get_llm_client())
    graph = await svc.get_dependency_graph(idea_id, tenant_id)
    return DependencyGraphResponse(**graph)


@router.get("/shared/dependencies", response_model=list[SharedDependencyResponse])
async def get_shared_dependencies(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)

    # Get user's ideas
    user_ideas = list(await db.scalars(
        select(Idea).where(
            Idea.tenant_id == tenant_id, Idea.creator_id == uuid.UUID(user_id)
        )
    ))
    user_idea_ids = [i.id for i in user_ideas]

    svc = DependencyService(db, get_llm_client())
    shared = await svc.get_shared_dependencies(tenant_id, user_idea_ids)
    return shared
