"""Port of Django's test_movies_viewset.py → pytest-asyncio + HTTPX."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cinema import Actor, Genre, Movie
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


async def test_movies_list_public(client: AsyncClient, movie: Movie):
    res = await client.get("/api/movies")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 1


async def test_movies_retrieve_public(client: AsyncClient, movie: Movie):
    res = await client.get(f"/api/movies/{movie.id}")
    assert res.status_code == 200
    assert res.json()["title"] == movie.title


async def test_movies_create_requires_auth(
    client: AsyncClient, genre_action: Genre, actor_one: Actor
):
    payload = {
        "title": "New Movie",
        "description": "",
        "duration": 90,
        "genres": [genre_action.id],
        "actors": [actor_one.id],
    }
    res = await client.post("/api/movies", json=payload)
    assert res.status_code in (401, 403)


async def test_movies_create_requires_admin(
    client: AsyncClient,
    regular_user,
    genre_action: Genre,
    actor_one: Actor,
):
    payload = {
        "title": "New Movie",
        "description": "",
        "duration": 90,
        "genres": [genre_action.id],
        "actors": [actor_one.id],
    }
    res = await client.post("/api/movies", json=payload, headers=auth_headers(regular_user))
    assert res.status_code == 403


async def test_movies_create_admin_success(
    client: AsyncClient,
    admin_user,
    genre_action: Genre,
    actor_one: Actor,
    db: AsyncSession,
):
    from sqlalchemy import select

    payload = {
        "title": "New Movie",
        "description": "D",
        "duration": 90,
        "genres": [genre_action.id],
        "actors": [actor_one.id],
    }
    res = await client.post("/api/movies", json=payload, headers=auth_headers(admin_user))
    assert res.status_code == 201
    result = await db.execute(select(Movie).where(Movie.title == "New Movie"))
    assert result.scalar_one_or_none() is not None


async def test_movies_update_admin(client: AsyncClient, admin_user, movie: Movie, db: AsyncSession):
    res = await client.patch(
        f"/api/movies/{movie.id}",
        json={"duration": 130},
        headers=auth_headers(admin_user),
    )
    assert res.status_code == 200
    await db.refresh(movie)
    assert movie.duration == 130


async def test_movies_delete_admin(client: AsyncClient, admin_user, movie: Movie, db: AsyncSession):
    from sqlalchemy import select, func

    res = await client.delete(f"/api/movies/{movie.id}", headers=auth_headers(admin_user))
    assert res.status_code == 204
    count = (await db.execute(select(func.count()).select_from(Movie))).scalar()
    assert count == 0


async def test_movies_filter_by_title(client: AsyncClient, movie: Movie):
    res = await client.get("/api/movies?title=Movie")
    assert res.status_code == 200
    assert res.json()["count"] == 1


async def test_movies_filter_by_genres(
    client: AsyncClient, db: AsyncSession, genre_action: Genre
):
    g2 = Genre(name="Drama")
    a2 = Actor(first_name="Amy", last_name="Adams")
    db.add_all([g2, a2])
    await db.commit()
    m2 = Movie(title="Movie B", description="", duration=100, genres=[g2], actors=[a2])
    db.add(m2)
    await db.commit()

    res = await client.get(f"/api/movies?genres={genre_action.id}")
    assert res.status_code == 200
    assert res.json()["count"] == 1


async def test_movies_filter_by_actors(client: AsyncClient, actor_one: Actor, movie: Movie):
    res = await client.get(f"/api/movies?actors={actor_one.id}")
    assert res.status_code == 200
    assert res.json()["count"] == 1


async def test_movies_search(client: AsyncClient, movie: Movie):
    res = await client.get("/api/movies?search=Desc")
    assert res.status_code == 200
    assert res.json()["count"] == 1


async def test_movies_ordering(client: AsyncClient, db: AsyncSession, movie: Movie):
    m2 = Movie(title="AAA", description="", duration=50)
    db.add(m2)
    await db.commit()
    res = await client.get("/api/movies?ordering=title")
    assert res.status_code == 200
    assert res.json()["results"][0]["title"] == "AAA"


async def test_movies_recommendations(client: AsyncClient, db: AsyncSession, movie: Movie):
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select

    m2 = Movie(title="Movie C", description="", duration=110)
    m2.genres = list(movie.genres)
    db.add(m2)
    await db.commit()

    res = await client.get(f"/api/movies/{movie.id}/recommendations")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
