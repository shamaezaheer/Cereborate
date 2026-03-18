"""Tests for planning session lifecycle and ideas CRUD."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


# ---------- Ideas CRUD Tests ----------

@pytest.mark.asyncio
async def test_create_idea(client: AsyncClient):
    """Test direct idea creation (bypassing planning session)."""
    # Register and login first
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "idea_user@example.com",
            "password": "password123",
            "display_name": "Idea User",
            "tenant_name": "Idea Corp",
            "tenant_slug": "idea-corp",
        },
    )
    token = reg.json()["token"]["access_token"]

    res = await client.post(
        "/api/v1/ideas",
        json={
            "title": "My Test Idea",
            "description": "A description of my idea",
            "total_budget": 10000,
            "budget_currency": "USD",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "My Test Idea"
    assert data["version"] == 1
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_list_ideas(client: AsyncClient):
    """Test listing owned ideas."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_user@example.com",
            "password": "password123",
            "display_name": "List User",
            "tenant_name": "List Corp",
            "tenant_slug": "list-corp",
        },
    )
    token = reg.json()["token"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Create 2 ideas
    await client.post("/api/v1/ideas", json={"title": "Idea A"}, headers=auth_headers)
    await client.post("/api/v1/ideas", json={"title": "Idea B"}, headers=auth_headers)

    res = await client.get("/api/v1/ideas", headers=auth_headers)
    assert res.status_code == 200
    ideas = res.json()
    assert len(ideas) == 2


@pytest.mark.asyncio
async def test_get_idea_detail(client: AsyncClient):
    """Test getting idea detail with components."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "detail_user@example.com",
            "password": "password123",
            "display_name": "Detail User",
            "tenant_name": "Detail Corp",
            "tenant_slug": "detail-corp",
        },
    )
    token = reg.json()["token"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    idea_res = await client.post(
        "/api/v1/ideas", json={"title": "Detail Idea"}, headers=auth_headers
    )
    idea_id = idea_res.json()["id"]

    # Add a component
    await client.post(
        f"/api/v1/ideas/{idea_id}/components",
        json={"name": "Backend API", "description": "FastAPI backend"},
        headers=auth_headers,
    )

    res = await client.get(f"/api/v1/ideas/{idea_id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Detail Idea"
    assert len(data["components"]) == 1
    assert data["components"][0]["name"] == "Backend API"


@pytest.mark.asyncio
async def test_update_idea(client: AsyncClient):
    """Test updating an idea increments version."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "update_user@example.com",
            "password": "password123",
            "display_name": "Update User",
            "tenant_name": "Update Corp",
            "tenant_slug": "update-corp",
        },
    )
    token = reg.json()["token"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    idea_res = await client.post(
        "/api/v1/ideas", json={"title": "Update Me"}, headers=auth_headers
    )
    idea_id = idea_res.json()["id"]

    res = await client.patch(
        f"/api/v1/ideas/{idea_id}",
        json={"title": "Updated Title", "status": "active"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Updated Title"
    assert data["version"] == 2


@pytest.mark.asyncio
async def test_archive_idea(client: AsyncClient):
    """Test archiving an idea removes it from list."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "archive_user@example.com",
            "password": "password123",
            "display_name": "Archive User",
            "tenant_name": "Archive Corp",
            "tenant_slug": "archive-corp",
        },
    )
    token = reg.json()["token"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    idea_res = await client.post(
        "/api/v1/ideas", json={"title": "Archive Me"}, headers=auth_headers
    )
    idea_id = idea_res.json()["id"]

    # Archive
    res = await client.delete(f"/api/v1/ideas/{idea_id}", headers=auth_headers)
    assert res.status_code == 204

    # Should not appear in list
    list_res = await client.get("/api/v1/ideas", headers=auth_headers)
    ids = [i["id"] for i in list_res.json()]
    assert idea_id not in ids


# ---------- Planning Session Tests (with mocked LLM) ----------

@pytest.mark.asyncio
async def test_planning_session_start(client: AsyncClient):
    """Test starting a planning session with mocked LLM."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "plan_test@example.com",
            "password": "password123",
            "display_name": "Plan User",
            "tenant_name": "Plan Corp",
            "tenant_slug": "plan-corp",
        },
    )
    token = reg.json()["token"]["access_token"]

    mock_extraction = {
        "title": "Mobile Water Tracker",
        "description": "An app to track daily water intake",
        "deadline": None,
        "total_budget": None,
        "budget_currency": "USD",
        "components": [
            {"name": "Mobile App", "description": "iOS/Android app", "priority": "must_have", "estimated_cost": None}
        ],
        "follow_up_question": "What platforms should the app support?",
        "is_complete": False,
    }

    with patch(
        "app.services.llm_service.LLMService.extract_idea_from_conversation",
        new_callable=AsyncMock,
    ) as mock_llm:
        from app.llm.schemas import ExtractedIdeaData
        mock_llm.return_value = ExtractedIdeaData.model_validate(mock_extraction)

        res = await client.post(
            "/api/v1/plan/start",
            json={"message": "I want to build a water tracker app"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "active"
    assert len(data["conversation_history"]) >= 1
    assert data["extracted_data"]["title"] == "Mobile Water Tracker"
