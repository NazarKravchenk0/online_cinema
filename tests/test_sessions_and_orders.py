import pytest

pytestmark = pytest.mark.django_db

def test_available_seats_action(api_client, session):
    res = api_client.get(f"/api/movie-sessions/{session.id}/available_seats/")
    assert res.status_code == 200
    assert res.data["session_id"] == session.id
    assert "available" in res.data

def test_create_order_with_tickets(api_client, user, session):
    api_client.force_authenticate(user=user)
    payload = {
        "tickets": [
            {"movie_session": session.id, "row": 1, "seat": 1},
            {"movie_session": session.id, "row": 1, "seat": 2},
        ]
    }
    res = api_client.post("/api/orders/", payload, format="json")
    assert res.status_code == 201

def test_double_booking_prevented(api_client, user, session):
    api_client.force_authenticate(user=user)
    payload = {"tickets": [{"movie_session": session.id, "row": 1, "seat": 1}]}
    res1 = api_client.post("/api/orders/", payload, format="json")
    assert res1.status_code == 201

    res2 = api_client.post("/api/orders/", payload, format="json")
    assert res2.status_code == 400
