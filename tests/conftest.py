"""
Async test fixtures using an in-memory SQLite database.
Each test gets a fresh, isolated database via function-scoped fixtures.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.cinema import Actor, CinemaHall, Genre, Movie, MovieSession
from app.models.user import User

# ── In-memory SQLite for tests ────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    TestSession = async_sessionmaker(db_engine, expire_on_commit=False)
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client wired to the test DB session."""
    app = create_app()

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── User fixtures ─────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user(db: AsyncSession) -> User:
    user = User(
        username="user",
        email="user@example.com",
        hashed_password=hash_password("userpass123"),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


# ── Domain fixtures ───────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def genre_action(db: AsyncSession) -> Genre:
    g = Genre(name="Action")
    db.add(g)
    await db.commit()
    await db.refresh(g)
    return g


@pytest_asyncio.fixture
async def actor_one(db: AsyncSession) -> Actor:
    a = Actor(first_name="Tom", last_name="Hardy")
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


@pytest_asyncio.fixture
async def movie(db: AsyncSession, genre_action: Genre, actor_one: Actor) -> Movie:
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select

    m = Movie(title="Movie A", description="Desc", duration=120)
    m.genres = [genre_action]
    m.actors = [actor_one]
    db.add(m)
    await db.commit()
    result = await db.execute(
        select(Movie)
        .where(Movie.id == m.id)
        .options(selectinload(Movie.genres), selectinload(Movie.actors))
    )
    return result.scalar_one()


@pytest_asyncio.fixture
async def hall(db: AsyncSession) -> CinemaHall:
    h = CinemaHall(name="Hall 1", rows=5, seats_in_row=5)
    db.add(h)
    await db.commit()
    await db.refresh(h)
    return h


@pytest_asyncio.fixture
async def session(db: AsyncSession, movie: Movie, hall: CinemaHall) -> MovieSession:
    ms = MovieSession(
        movie_id=movie.id,
        cinema_hall_id=hall.id,
        show_time=datetime.now(timezone.utc) + timedelta(days=1),
        price=Decimal("10.00"),
    )
    db.add(ms)
    await db.commit()
    await db.refresh(ms)
    return ms
