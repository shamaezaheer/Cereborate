"""Team API — shared idea browsing, Q&A, and notifications."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.shareability import (
    filter_ideas_by_access,
    get_user_access_tier,
)
from app.deps import get_current_user_id, get_db
from app.llm.client import get_llm_client
from app.models.dependency import ComponentDependency
from app.models.idea import Idea, IdeaComponent
from app.models.user import TenantMembership
from app.schemas.team import (
    AnswerCreate,
    AnswerResponse,
    NotificationResponse,
    QuestionCreate,
    QuestionResponse,
    SharedIdeaDetailResponse,
    SharedIdeaResponse,
)
from app.services.notification_service import NotificationService
from app.services.question_service import QuestionService
from app.services.shareability_service import ShareabilityService

router = APIRouter(tags=["team"])


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_membership(
    user_id: str, db: AsyncSession
) -> TenantMembership:
    membership = await db.scalar(
        select(TenantMembership).where(
            TenantMembership.user_id == uuid.UUID(user_id)
        )
    )
    if not membership:
        raise HTTPException(status_code=400, detail="No tenant membership found")
    return membership


# ─── Shared Ideas ─────────────────────────────────────────────────────────────

@router.get("/shared/ideas", response_model=list[SharedIdeaResponse])
async def browse_shared_ideas(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Browse ideas shared with this user (not owned by them, tier-filtered)."""
    membership = await _get_membership(user_id, db)
    tenant_id = membership.tenant_id
    uid = uuid.UUID(user_id)

    # Start with all active ideas in tenant, excluding the user's own
    base_q = select(Idea).where(
        Idea.tenant_id == tenant_id,
        Idea.creator_id != uid,
        Idea.status != "archived",
    )

    # Apply shareability filter
    base_q = filter_ideas_by_access(
        base_q, uid, membership.access_tier, tenant_id, Idea.id
    )

    ideas = list(await db.scalars(base_q))

    svc = ShareabilityService(db, get_llm_client())
    result = []
    for idea in ideas:
        index = await svc.compute_shareability_index(idea.id)
        # Count confirmed cross-idea deps touching this idea
        comps = list(await db.scalars(
            select(IdeaComponent).where(IdeaComponent.idea_id == idea.id)
        ))
        comp_ids = {c.id for c in comps}
        cross_deps = list(await db.scalars(
            select(ComponentDependency).where(
                ComponentDependency.tenant_id == tenant_id,
                ComponentDependency.is_cross_idea.is_(True),
                ComponentDependency.confirmed.is_(True),
            )
        ))
        shared_dep_count = sum(
            1 for d in cross_deps
            if d.source_component_id in comp_ids or d.target_component_id in comp_ids
        )
        result.append(SharedIdeaResponse(
            id=idea.id,
            title=idea.title,
            description=idea.description,
            status=idea.status,
            shareability_index=index,
            shared_dep_count=shared_dep_count,
            creator_id=idea.creator_id,
        ))
    return result


@router.get("/shared/ideas/{idea_id}", response_model=SharedIdeaDetailResponse)
async def get_shared_idea(
    idea_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get shared idea detail — components filtered by access tier, no budget."""
    membership = await _get_membership(user_id, db)
    tenant_id = membership.tenant_id
    uid = uuid.UUID(user_id)

    idea = await db.scalar(
        select(Idea).where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    user_tier = await get_user_access_tier(db, uid, tenant_id)
    svc = ShareabilityService(db, get_llm_client())
    info = await svc.get_idea_shareability(idea_id, tenant_id)

    # Filter components by access tier and exclude budget
    rule_by_comp = {cs["component_id"]: cs for cs in info["component_scores"]}
    all_comps = list(await db.scalars(
        select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
    ))

    visible_components = []
    for comp in all_comps:
        cs = rule_by_comp.get(comp.id)
        min_tier = cs["min_access_tier"] if cs else 1
        if user_tier >= min_tier:
            visible_components.append({
                "id": str(comp.id),
                "name": comp.name,
                "description": comp.description,
                "status": comp.status,
                "priority": comp.priority,
                "deadline": comp.deadline.isoformat() if comp.deadline else None,
                # budget deliberately excluded
            })

    return SharedIdeaDetailResponse(
        id=idea.id,
        title=idea.title,
        description=idea.description,
        status=idea.status,
        deadline=idea.deadline,
        components=visible_components,
        shareability_index=info["shareability_index"],
    )


@router.get("/shared/ideas/{idea_id}/dependencies")
async def get_shared_idea_dependencies(
    idea_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get cross-idea shared dependencies for a specific shared idea."""
    membership = await _get_membership(user_id, db)
    tenant_id = membership.tenant_id

    idea = await db.scalar(
        select(Idea).where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    comps = list(await db.scalars(
        select(IdeaComponent).where(IdeaComponent.idea_id == idea_id)
    ))
    comp_ids = {c.id for c in comps}

    cross_deps = list(await db.scalars(
        select(ComponentDependency).where(
            ComponentDependency.tenant_id == tenant_id,
            ComponentDependency.is_cross_idea.is_(True),
            ComponentDependency.confirmed.is_(True),
        )
    ))

    relevant = [
        d for d in cross_deps
        if d.source_component_id in comp_ids or d.target_component_id in comp_ids
    ]

    result = []
    for dep in relevant:
        source = await db.get(IdeaComponent, dep.source_component_id)
        target = await db.get(IdeaComponent, dep.target_component_id)
        if source and target:
            result.append({
                "dependency_id": str(dep.id),
                "dependency_type": dep.dependency_type,
                "source": {
                    "id": str(source.id),
                    "name": source.name,
                    "description": source.description,
                    "status": source.status,
                    "deadline": source.deadline.isoformat() if source.deadline else None,
                    "idea_id": str(source.idea_id),
                },
                "target": {
                    "id": str(target.id),
                    "name": target.name,
                    "description": target.description,
                    "status": target.status,
                    "deadline": target.deadline.isoformat() if target.deadline else None,
                    "idea_id": str(target.idea_id),
                },
            })
    return result


# ─── Questions ────────────────────────────────────────────────────────────────

@router.post(
    "/shared/ideas/{idea_id}/questions",
    response_model=QuestionResponse,
    status_code=201,
)
async def ask_question(
    idea_id: uuid.UUID,
    data: QuestionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    membership = await _get_membership(user_id, db)
    svc = QuestionService(db, get_llm_client())
    try:
        question = await svc.ask_question(
            idea_id=idea_id,
            asked_by=uuid.UUID(user_id),
            question_text=data.question_text,
            tenant_id=membership.tenant_id,
            component_id=data.component_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return QuestionResponse.model_validate(question)


@router.get("/shared/ideas/{idea_id}/questions", response_model=list[QuestionResponse])
async def list_questions(
    idea_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    membership = await _get_membership(user_id, db)
    uid = uuid.UUID(user_id)
    user_tier = await get_user_access_tier(db, uid, membership.tenant_id)
    svc = QuestionService(db, get_llm_client())
    questions = await svc.get_questions(idea_id, membership.tenant_id, user_tier)
    return [QuestionResponse.model_validate(q) for q in questions]


@router.get("/questions/{question_id}/answers", response_model=list[AnswerResponse])
async def list_answers(
    question_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    membership = await _get_membership(user_id, db)
    svc = QuestionService(db, get_llm_client())
    try:
        answers = await svc.get_answers(question_id, membership.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [AnswerResponse.model_validate(a) for a in answers]


@router.post(
    "/questions/{question_id}/answers",
    response_model=AnswerResponse,
    status_code=201,
)
async def submit_answer(
    question_id: uuid.UUID,
    data: AnswerCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    membership = await _get_membership(user_id, db)
    svc = QuestionService(db, get_llm_client())
    try:
        answer = await svc.answer_question(
            question_id=question_id,
            answered_by=uuid.UUID(user_id),
            answer_text=data.answer_text,
            tenant_id=membership.tenant_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return AnswerResponse.model_validate(answer)


@router.post(
    "/questions/{question_id}/answers/ai",
    response_model=AnswerResponse,
    status_code=201,
)
async def request_ai_answer(
    question_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Request an LLM-generated answer (requires owner approval)."""
    membership = await _get_membership(user_id, db)
    svc = QuestionService(db, get_llm_client())
    try:
        answer = await svc.generate_ai_answer(question_id, membership.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return AnswerResponse.model_validate(answer)


@router.patch("/answers/{answer_id}/approve", response_model=AnswerResponse)
async def approve_answer(
    answer_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Idea owner approves an AI-generated answer."""
    membership = await _get_membership(user_id, db)
    svc = QuestionService(db, get_llm_client())
    try:
        answer = await svc.approve_answer(
            answer_id, uuid.UUID(user_id), membership.tenant_id
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    return AnswerResponse.model_validate(answer)


# ─── Notifications ────────────────────────────────────────────────────────────

@router.get("/notifications", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    membership = await _get_membership(user_id, db)
    svc = NotificationService(db)
    notifs = await svc.get_notifications(
        uuid.UUID(user_id), membership.tenant_id, unread_only=unread_only
    )
    return [NotificationResponse.model_validate(n) for n in notifs]


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    membership = await _get_membership(user_id, db)
    svc = NotificationService(db)
    try:
        notif = await svc.mark_read(
            notification_id, uuid.UUID(user_id), membership.tenant_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return NotificationResponse.model_validate(notif)
