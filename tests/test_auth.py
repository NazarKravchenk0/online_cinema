"""JWT authentication endpoint tests."""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_obtain_token_success(client: AsyncClient, regular_user):
    res = await client.post(
        "/api/auth/token",
        json={"username": "user", "password": "userpass123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_obtain_token_bad_password(client: AsyncClient, regular_user):
    res = await client.post(
        "/api/auth/token",
        json={"username": "user", "password": "wrongpassword"},
    )
    assert res.status_code == 401


async def test_obtain_token_unknown_user(client: AsyncClient):
    res = await client.post(
        "/api/auth/token",
        json={"username": "nobody", "password": "whatever"},
    )
    assert res.status_code == 401


async def test_refresh_token(client: AsyncClient, regular_user):
    obtain = await client.post(
        "/api/auth/token",
        json={"username": "user", "password": "userpass123"},
    )
    refresh_token = obtain.json()["refresh_token"]
    res = await client.post("/api/auth/token/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.json()


async def test_refresh_with_access_token_rejected(client: AsyncClient, regular_user):
    obtain = await client.post(
        "/api/auth/token",
        json={"username": "user", "password": "userpass123"},
    )
    access_token = obtain.json()["access_token"]
    res = await client.post("/api/auth/token/refresh", json={"refresh_token": access_token})
    assert res.status_code == 401
