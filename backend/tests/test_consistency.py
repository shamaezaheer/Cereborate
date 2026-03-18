"""Tests for consistency checking — budget, deadlines, component overlap."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


async def _setup_idea_with_components(client: AsyncClient, suffix: str):
    """Helper: create user, idea, and components."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"cons_{suffix}@example.com",
            "password": "password123",
            "display_name": "Test",
            "tenant_name": f"Cons Corp {suffix}",
            "tenant_slug": f"cons-corp-{suffix}",
        },
    )
    token = reg.json()["token"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    idea = await client.post(
        "/api/v1/ideas",
        json={"title": "Test Idea", "total_budget": 10000},
        headers=auth,
    )
    idea_id = idea.json()["id"]

    return token, auth, idea_id


@pytest.mark.asyncio
async def test_budget_consistency_flag(client: AsyncClient):
    """Test that exceeding budget creates a flag."""
    token, auth, idea_id = await _setup_idea_with_components(client, "budget")

    # Add components with total cost > budget
    await client.post(
        f"/api/v1/ideas/{idea_id}/components",
        json={"name": "Component A", "description": "A", "estimated_cost": 7000},
        headers=auth,
    )
    await client.post(
        f"/api/v1/ideas/{idea_id}/components",
        json={"name": "Component B", "description": "B", "estimated_cost": 5000},
        headers=auth,
    )

    # Manually trigger consistency check (with mocked LLM)
    with patch(
        "app.services.consistency_service.ConsistencyService._check_llm_consistency",
        new_callable=AsyncMock,
        return_value=[],
    ):
        res = await client.post(
            f"/api/v1/ideas/{idea_id}/consistency/check",
            headers=auth,
        )

    assert res.status_code == 200
    flags = res.json()
    budget_flags = [f for f in flags if f["flag_type"] == "budget_exceeds_total"]
    assert len(budget_flags) == 1
    assert budget_flags[0]["severity"] == "warning"


@pytest.mark.asyncio
async def test_consistency_check_no_issues(client: AsyncClient):
    """Test that a valid idea returns no flags."""
    token, auth, idea_id = await _setup_idea_with_components(client, "noissue")

    # Add a component within budget
    await client.post(
        f"/api/v1/ideas/{idea_id}/components",
        json={"name": "Small Component", "description": "Cheap", "estimated_cost": 1000},
        headers=auth,
    )

    with patch(
        "app.services.consistency_service.ConsistencyService._check_llm_consistency",
        new_callable=AsyncMock,
        return_value=[],
    ), patch(
        "app.services.consistency_service.ConsistencyService._check_component_overlap",
        new_callable=AsyncMock,
        return_value=[],
    ):
        res = await client.post(
            f"/api/v1/ideas/{idea_id}/consistency/check",
            headers=auth,
        )

    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_get_consistency_flags(client: AsyncClient):
    """Test fetching existing flags for an idea."""
    token, auth, idea_id = await _setup_idea_with_components(client, "getflags")

    # Create a flag via exceeded budget
    await client.post(
        f"/api/v1/ideas/{idea_id}/components",
        json={"name": "Expensive", "estimated_cost": 99999},
        headers=auth,
    )

    with patch(
        "app.services.consistency_service.ConsistencyService._check_llm_consistency",
        new_callable=AsyncMock,
        return_value=[],
    ), patch(
        "app.services.consistency_service.ConsistencyService._check_component_overlap",
        new_callable=AsyncMock,
        return_value=[],
    ):
        await client.post(f"/api/v1/ideas/{idea_id}/consistency/check", headers=auth)

    res = await client.get(f"/api/v1/ideas/{idea_id}/consistency", headers=auth)
    assert res.status_code == 200
    flags = res.json()
    assert any(f["flag_type"] == "budget_exceeds_total" for f in flags)
