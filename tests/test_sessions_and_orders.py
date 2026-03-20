"""Port of Django's test_sessions_and_orders.py → pytest-asyncio + HTTPX."""
import pytest
from httpx import AsyncClient

from app.models.cinema import MovieSession
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


async def test_available_seats_action(client: AsyncClient, session: MovieSession):
    res = await client.get(f"/api/movie-sessions/{session.id}/available_seats")
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == session.id
    assert "available" in data
    # All 25 seats (5×5 hall) should be free
    total_free = sum(len(row["seats"]) for row in data["available"])
    assert total_free == 25


async def test_create_order_with_tickets(
    client: AsyncClient, regular_user, session: MovieSession
):
    payload = {
        "tickets": [
            {"movie_session": session.id, "row": 1, "seat": 1},
            {"movie_session": session.id, "row": 1, "seat": 2},
        ]
    }
    res = await client.post("/api/orders", json=payload, headers=auth_headers(regular_user))
    assert res.status_code == 201
    data = res.json()
    assert len(data["tickets"]) == 2


async def test_create_order_requires_auth(client: AsyncClient, session: MovieSession):
    payload = {"tickets": [{"movie_session": session.id, "row": 1, "seat": 1}]}
    res = await client.post("/api/orders", json=payload)
    assert res.status_code == 401


async def test_double_booking_prevented(
    client: AsyncClient, regular_user, session: MovieSession
):
    payload = {"tickets": [{"movie_session": session.id, "row": 1, "seat": 1}]}
    res1 = await client.post("/api/orders", json=payload, headers=auth_headers(regular_user))
    assert res1.status_code == 201

    res2 = await client.post("/api/orders", json=payload, headers=auth_headers(regular_user))
    assert res2.status_code == 400


async def test_order_user_scoping(
    client: AsyncClient,
    regular_user,
    admin_user,
    session: MovieSession,
):
    """Regular users only see their own orders; admins see all."""
    # Create order as regular user
    payload = {"tickets": [{"movie_session": session.id, "row": 2, "seat": 1}]}
    await client.post("/api/orders", json=payload, headers=auth_headers(regular_user))

    # Regular user sees 1 order
    res_user = await client.get("/api/orders", headers=auth_headers(regular_user))
    assert res_user.status_code == 200
    assert res_user.json()["count"] == 1

    # Admin sees all orders
    res_admin = await client.get("/api/orders", headers=auth_headers(admin_user))
    assert res_admin.status_code == 200
    assert res_admin.json()["count"] >= 1


async def test_available_seats_decreases_after_booking(
    client: AsyncClient, regular_user, session: MovieSession
):
    payload = {"tickets": [{"movie_session": session.id, "row": 1, "seat": 1}]}
    await client.post("/api/orders", json=payload, headers=auth_headers(regular_user))

    res = await client.get(f"/api/movie-sessions/{session.id}/available_seats")
    data = res.json()
    row1 = next(r for r in data["available"] if r["row"] == 1)
    assert 1 not in row1["seats"]


async def test_invalid_seat_rejected(
    client: AsyncClient, regular_user, session: MovieSession
):
    payload = {"tickets": [{"movie_session": session.id, "row": 99, "seat": 99}]}
    res = await client.post("/api/orders", json=payload, headers=auth_headers(regular_user))
    assert res.status_code == 400
