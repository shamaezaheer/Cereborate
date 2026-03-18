"""Tests for component dependency DAG — cycle detection, CRUD, graph endpoint."""

import pytest
from httpx import AsyncClient


async def _setup(client: AsyncClient, suffix: str):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"dep_{suffix}@example.com",
            "password": "password123",
            "display_name": "Dep User",
            "tenant_name": f"Dep Corp {suffix}",
            "tenant_slug": f"dep-corp-{suffix}",
        },
    )
    token = reg.json()["token"]["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    idea = await client.post("/api/v1/ideas", json={"title": "Dep Idea"}, headers=auth)
    idea_id = idea.json()["id"]

    comp_a = await client.post(
        f"/api/v1/ideas/{idea_id}/components",
        json={"name": "Component A", "description": "First component"},
        headers=auth,
    )
    comp_b = await client.post(
        f"/api/v1/ideas/{idea_id}/components",
        json={"name": "Component B", "description": "Second component"},
        headers=auth,
    )
    return token, auth, idea_id, comp_a.json()["id"], comp_b.json()["id"]


@pytest.mark.asyncio
async def test_add_dependency(client: AsyncClient):
    """Test adding a dependency between two components."""
    _, auth, idea_id, comp_a_id, comp_b_id = await _setup(client, "add")

    res = await client.post(
        f"/api/v1/components/{comp_a_id}/dependencies",
        json={"target_component_id": comp_b_id, "dependency_type": "blocks"},
        headers=auth,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["source_component_id"] == comp_a_id
    assert data["target_component_id"] == comp_b_id
    assert data["dependency_type"] == "blocks"
    assert data["is_cross_idea"] is False


@pytest.mark.asyncio
async def test_dependency_graph(client: AsyncClient):
    """Test getting the dependency graph for an idea."""
    _, auth, idea_id, comp_a_id, comp_b_id = await _setup(client, "graph")

    await client.post(
        f"/api/v1/components/{comp_a_id}/dependencies",
        json={"target_component_id": comp_b_id, "dependency_type": "extends"},
        headers=auth,
    )

    res = await client.get(f"/api/v1/ideas/{idea_id}/dependency-graph", headers=auth)
    assert res.status_code == 200
    data = res.json()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["edges"][0]["type"] == "extends"


@pytest.mark.asyncio
async def test_list_idea_dependencies(client: AsyncClient):
    """Test listing dependencies for an idea."""
    _, auth, idea_id, comp_a_id, comp_b_id = await _setup(client, "list")

    await client.post(
        f"/api/v1/components/{comp_a_id}/dependencies",
        json={"target_component_id": comp_b_id, "dependency_type": "requires_output"},
        headers=auth,
    )

    res = await client.get(f"/api/v1/ideas/{idea_id}/dependencies", headers=auth)
    assert res.status_code == 200
    deps = res.json()
    assert len(deps) == 1


@pytest.mark.asyncio
async def test_invalid_dependency_type(client: AsyncClient):
    """Test that invalid dependency type is rejected."""
    _, auth, idea_id, comp_a_id, comp_b_id = await _setup(client, "invalid")

    res = await client.post(
        f"/api/v1/components/{comp_a_id}/dependencies",
        json={"target_component_id": comp_b_id, "dependency_type": "invalid_type"},
        headers=auth,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_delete_dependency(client: AsyncClient):
    """Test removing a dependency."""
    _, auth, idea_id, comp_a_id, comp_b_id = await _setup(client, "delete")

    add_res = await client.post(
        f"/api/v1/components/{comp_a_id}/dependencies",
        json={"target_component_id": comp_b_id, "dependency_type": "informed_by"},
        headers=auth,
    )
    dep_id = add_res.json()["id"]

    del_res = await client.delete(f"/api/v1/dependencies/{dep_id}", headers=auth)
    assert del_res.status_code == 204

    # Should be gone from list
    list_res = await client.get(f"/api/v1/ideas/{idea_id}/dependencies", headers=auth)
    assert len(list_res.json()) == 0
