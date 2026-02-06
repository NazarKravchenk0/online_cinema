import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from apps.cinema.models import Genre, Actor, Movie, CinemaHall, MovieSession
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

@pytest.fixture()
def api_client():
    return APIClient()

@pytest.fixture()
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )

@pytest.fixture()
def user(db):
    return User.objects.create_user(
        username="user",
        email="user@example.com",
        password="userpass123",
    )

@pytest.fixture()
def genre_action(db):
    return Genre.objects.create(name="Action")

@pytest.fixture()
def actor_one(db):
    return Actor.objects.create(first_name="Tom", last_name="Hardy")

@pytest.fixture()
def movie(db, genre_action, actor_one):
    m = Movie.objects.create(title="Movie A", description="Desc", duration=120)
    m.genres.add(genre_action)
    m.actors.add(actor_one)
    return m

@pytest.fixture()
def hall(db):
    return CinemaHall.objects.create(name="Hall 1", rows=5, seats_in_row=5)

@pytest.fixture()
def session(db, movie, hall):
    return MovieSession.objects.create(
        movie=movie,
        cinema_hall=hall,
        show_time=timezone.now() + timedelta(days=1),
        price=Decimal("10.00"),
    )
