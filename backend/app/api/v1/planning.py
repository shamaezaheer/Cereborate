import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user_id, get_db
from app.llm.client import get_llm_client
from app.models.user import TenantMembership
from app.schemas.idea import IdeaResponse
from app.schemas.planning import (
    SessionCompleteResponse,
    SessionRespondRequest,
    SessionResponse,
    SessionStartRequest,
)
from app.services.planning_service import PlanningService

router = APIRouter(prefix="/plan", tags=["planning"])


async def _get_tenant_id(user_id: str, db: AsyncSession) -> uuid.UUID:
    membership = await db.scalar(
        select(TenantMembership).where(TenantMembership.user_id == uuid.UUID(user_id))
    )
    if not membership:
        raise HTTPException(status_code=400, detail="No tenant membership found")
    return membership.tenant_id


@router.post("/start", response_model=SessionResponse, status_code=201)
async def start_session(
    data: SessionStartRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = await _get_tenant_id(user_id, db)
    svc = PlanningService(db, get_llm_client())
    session = await svc.start_session(uuid.UUID(user_id), tenant_id, data.message)
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/respond", response_model=SessionResponse)
async def respond_to_session(
    session_id: uuid.UUID,
    data: SessionRespondRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PlanningService(db, get_llm_client())
    try:
        session, _ = await svc.respond(session_id, data.message)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/complete", response_model=SessionCompleteResponse)
async def complete_session(
    session_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PlanningService(db, get_llm_client())
    try:
        session, idea = await svc.complete_session(session_id, uuid.UUID(user_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return SessionCompleteResponse(
        session=SessionResponse.model_validate(session),
        idea=IdeaResponse.model_validate(idea),
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PlanningService(db, get_llm_client())
    session = await svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.model_validate(session)
