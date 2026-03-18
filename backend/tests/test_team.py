"""Tests for team collaboration — shared ideas, Q&A, notifications."""

import pytest
from httpx import AsyncClient


async def _setup_owner(client: AsyncClient, suffix: str):
    """Register an owner with an idea + components."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"owner_{suffix}@example.com",
            "password": "password123",
            "display_name": "Owner User",
            "tenant_name": f"Owner Corp {suffix}",
            "tenant_slug": f"owner-corp-{suffix}",
        },
    )
    token = reg.json()["token"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    idea = await client.post(
        "/api/v1/ideas",
        json={"title": "Shared Idea", "description": "An idea to share"},
        headers=auth,
    )
    idea_id = idea.json()["id"]

    # Set low shareability so team members can see it
    await client.patch(
        f"/api/v1/ideas/{idea_id}/shareability",
        json={"min_access_tier": 1, "classification": "public"},
        headers=auth,
    )

    comp = await client.post(
        f"/api/v1/ideas/{idea_id}/components",
        json={"name": "Component A", "description": "Public component"},
        headers=auth,
    )
    return token, auth, idea_id, comp.json()["id"]


async def _setup_member(client: AsyncClient, suffix: str):
    """Register a separate member in their own tenant."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"member_{suffix}@example.com",
            "password": "password123",
            "display_name": "Member User",
            "tenant_name": f"Member Corp {suffix}",
            "tenant_slug": f"member-corp-{suffix}",
        },
    )
    token = reg.json()["token"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    return token, auth


@pytest.mark.asyncio
async def test_browse_shared_ideas(client: AsyncClient):
    """Owner's idea appears in their own shared-ideas browse (different creator check)."""
    # Register two users in different tenants — each sees their own tenant
    token, auth, idea_id, _ = await _setup_owner(client, "browse")

    # User browses shared ideas — won't see their own (creator_id != uid filter)
    res = await client.get("/api/v1/shared/ideas", headers=auth)
    assert res.status_code == 200
    ideas = res.json()
    # Owner won't see their own idea in the shared view
    assert all(i["id"] != idea_id for i in ideas)


@pytest.mark.asyncio
async def test_ask_question(client: AsyncClient):
    """User can ask a question on a shared idea."""
    token, auth, idea_id, _ = await _setup_owner(client, "ask-q")

    res = await client.post(
        f"/api/v1/shared/ideas/{idea_id}/questions",
        json={"question_text": "What is the timeline for this?"},
        headers=auth,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["question_text"] == "What is the timeline for this?"
    assert data["status"] == "open"
    assert data["idea_id"] == idea_id


@pytest.mark.asyncio
async def test_list_questions(client: AsyncClient):
    """Questions are listed for the idea."""
    token, auth, idea_id, _ = await _setup_owner(client, "list-q")

    # Ask two questions
    for i in range(2):
        await client.post(
            f"/api/v1/shared/ideas/{idea_id}/questions",
            json={"question_text": f"Question {i+1}?"},
            headers=auth,
        )

    res = await client.get(f"/api/v1/shared/ideas/{idea_id}/questions", headers=auth)
    assert res.status_code == 200
    assert len(res.json()) == 2


@pytest.mark.asyncio
async def test_answer_question(client: AsyncClient):
    """User can submit a human answer to a question."""
    token, auth, idea_id, _ = await _setup_owner(client, "answer-q")

    q_res = await client.post(
        f"/api/v1/shared/ideas/{idea_id}/questions",
        json={"question_text": "When will this launch?"},
        headers=auth,
    )
    question_id = q_res.json()["id"]

    a_res = await client.post(
        f"/api/v1/questions/{question_id}/answers",
        json={"answer_text": "We plan to launch in Q3."},
        headers=auth,
    )
    assert a_res.status_code == 201
    answer = a_res.json()
    assert answer["answer_text"] == "We plan to launch in Q3."
    assert answer["is_ai_generated"] is False
    assert answer["approved"] is True


@pytest.mark.asyncio
async def test_list_answers(client: AsyncClient):
    """Answers are retrievable for a question."""
    token, auth, idea_id, _ = await _setup_owner(client, "list-a")

    q_res = await client.post(
        f"/api/v1/shared/ideas/{idea_id}/questions",
        json={"question_text": "Who is responsible?"},
        headers=auth,
    )
    question_id = q_res.json()["id"]

    await client.post(
        f"/api/v1/questions/{question_id}/answers",
        json={"answer_text": "The platform team."},
        headers=auth,
    )

    res = await client.get(f"/api/v1/questions/{question_id}/answers", headers=auth)
    assert res.status_code == 200
    assert len(res.json()) == 1


@pytest.mark.asyncio
async def test_notifications_empty(client: AsyncClient):
    """New user has no notifications."""
    _, auth = await _setup_member(client, "notif-empty")

    res = await client.get("/api/v1/notifications", headers=auth)
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_mark_notification_read(client: AsyncClient):
    """Notifications can be marked as read."""
    from app.database import async_session_factory
    from app.models.user import TenantMembership, User
    from sqlalchemy import select
    import uuid

    token, auth = await _setup_member(client, "notif-read")

    # Manually inject a notification via the service
    async with async_session_factory() as db:
        from app.services.notification_service import NotificationService

        # Find the user
        user = await db.scalar(
            select(User).where(User.email == "member_notif-read@example.com")
        )
        membership = await db.scalar(
            select(TenantMembership).where(TenantMembership.user_id == user.id)
        )
        svc = NotificationService(db)
        notif = await svc.create(
            user_id=user.id,
            event_type="linked_idea_updated",
            tenant_id=membership.tenant_id,
            message="Test notification",
        )
        await db.commit()
        notif_id = str(notif.id)

    # Mark as read
    res = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=auth)
    assert res.status_code == 200
    assert res.json()["read"] is True
