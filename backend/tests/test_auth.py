import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # 1. Register new user
    reg_response = await client.post("/api/v1/auth/register", json={
        "name": "Test Engineer",
        "email": "engineer@patchpilot.io",
        "password": "StrongPassword123!",
    })
    assert reg_response.status_code == 201
    data = reg_response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "engineer@patchpilot.io"

    token = data["access_token"]

    # 2. Prevent duplicate email registration
    dup_response = await client.post("/api/v1/auth/register", json={
        "name": "Duplicate User",
        "email": "engineer@patchpilot.io",
        "password": "StrongPassword123!",
    })
    assert dup_response.status_code == 400

    # 3. Login
    login_response = await client.post("/api/v1/auth/login", json={
        "email": "engineer@patchpilot.io",
        "password": "StrongPassword123!",
    })
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data

    # 4. Access protected /auth/me route
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["name"] == "Test Engineer"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/projects")
    assert response.status_code == 401

