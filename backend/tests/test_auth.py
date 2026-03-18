import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User",
            "tenant_name": "Test Corp",
            "tenant_slug": "test-corp",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["email"] == "test@example.com"
    assert data["tenant"]["slug"] == "test-corp"
    assert "access_token" in data["token"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dup@example.com",
        "password": "password123",
        "display_name": "User",
        "tenant_name": "Tenant A",
        "tenant_slug": "tenant-a",
    }
    await client.post("/api/v1/auth/register", json=payload)

    # Second registration with same email
    payload2 = {**payload, "tenant_slug": "tenant-b", "tenant_name": "Tenant B"}
    res = await client.post("/api/v1/auth/register", json=payload2)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "display_name": "Login User",
            "tenant_name": "Login Corp",
            "tenant_slug": "login-corp",
        },
    )

    # Then login
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data["token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "password123",
            "display_name": "Wrong",
            "tenant_name": "Wrong Corp",
            "tenant_slug": "wrong-corp",
        },
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "badpassword"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "password": "password123",
            "display_name": "Me User",
            "tenant_name": "Me Corp",
            "tenant_slug": "me-corp",
        },
    )
    token = reg.json()["token"]["access_token"]

    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"] == "me@example.com"
    assert data["role"] == "owner"
    assert data["access_tier"] == 10
