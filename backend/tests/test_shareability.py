"""Tests for shareability — classification, index computation, access filtering."""

import pytest
from httpx import AsyncClient


async def _setup(client: AsyncClient, suffix: str):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"share_{suffix}@example.com",
            "password": "password123",
            "display_name": "Share User",
            "tenant_name": f"Share Corp {suffix}",
            "tenant_slug": f"share-corp-{suffix}",
        },
    )
    token = reg.json()["token"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    idea = await client.post(
        "/api/v1/ideas", json={"title": "Share Idea", "description": "Test idea"}, headers=auth
    )
    idea_id = idea.json()["id"]

    comp = await client.post(
        f"/api/v1/ideas/{idea_id}/components",
        json={"name": "Secret Component", "description": "Very confidential work"},
        headers=auth,
    )
    return token, auth, idea_id, comp.json()["id"]


@pytest.mark.asyncio
async def test_get_shareability(client: AsyncClient):
    """Test getting shareability info for an idea."""
    _, auth, idea_id, comp_id = await _setup(client, "get")

    res = await client.get(f"/api/v1/ideas/{idea_id}/shareability", headers=auth)
    assert res.status_code == 200
    data = res.json()
    assert data["idea_id"] == idea_id
    assert "shareability_index" in data
    assert isinstance(data["component_scores"], list)


@pytest.mark.asyncio
async def test_update_idea_shareability(client: AsyncClient):
    """Test updating idea-level shareability rule."""
    _, auth, idea_id, _ = await _setup(client, "update-idea")

    res = await client.patch(
        f"/api/v1/ideas/{idea_id}/shareability",
        json={"min_access_tier": 5, "classification": "confidential"},
        headers=auth,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["min_access_tier"] == 5
    assert data["classification"] == "confidential"
    assert data["auto_classified"] is False


@pytest.mark.asyncio
async def test_update_component_shareability(client: AsyncClient):
    """Test overriding component shareability."""
    _, auth, idea_id, comp_id = await _setup(client, "update-comp")

    res = await client.patch(
        f"/api/v1/components/{comp_id}/shareability",
        json={"min_access_tier": 7, "classification": "restricted"},
        headers=auth,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["min_access_tier"] == 7
    assert data["classification"] == "restricted"
    assert data["component_id"] == comp_id


@pytest.mark.asyncio
async def test_shareability_index_computation(client: AsyncClient):
    """Test that shareability index is computed from component scores."""
    _, auth, idea_id, comp_id = await _setup(client, "index")

    # Add another component
    await client.post(
        f"/api/v1/ideas/{idea_id}/components",
        json={"name": "Public Component", "description": "Open work"},
        headers=auth,
    )

    res = await client.get(f"/api/v1/ideas/{idea_id}/shareability", headers=auth)
    assert res.status_code == 200
    data = res.json()
    assert 0.0 <= data["shareability_index"] <= 1.0
    assert len(data["component_scores"]) == 2
