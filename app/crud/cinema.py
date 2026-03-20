"""CRUD helpers for cinema resources (async SQLAlchemy)."""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, or_, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cinema import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
    Ticket,
    movie_actors,
    movie_genres,
)
from app.models.user import User


# ── Generic helpers ───────────────────────────────────────────────────────────

async def get_or_404(db: AsyncSession, model, obj_id: int):
    obj = await db.get(model, obj_id)
    if obj is None:
        raise LookupError(f"{model.__name__} #{obj_id} not found")
    return obj


# ── Genre ─────────────────────────────────────────────────────────────────────

async def list_genres(db: AsyncSession, search: str | None, ordering: str | None) -> list[Genre]:
    q = select(Genre)
    if search:
        q = q.where(Genre.name.ilike(f"%{search}%"))
    if ordering:
        field = ordering.lstrip("-")
        col = getattr(Genre, field, None)
        if col is not None:
            q = q.order_by(col.desc() if ordering.startswith("-") else col)
    else:
        q = q.order_by(Genre.name)
    return list((await db.execute(q)).scalars().all())


async def create_genre(db: AsyncSession, name: str) -> Genre:
    obj = Genre(name=name)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def update_genre(db: AsyncSession, obj: Genre, data: dict) -> Genre:
    for k, v in data.items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


async def delete_genre(db: AsyncSession, obj: Genre) -> None:
    await db.delete(obj)
    await db.commit()


# ── Actor ─────────────────────────────────────────────────────────────────────

async def list_actors(db: AsyncSession, search: str | None, ordering: str | None) -> list[Actor]:
    q = select(Actor)
    if search:
        q = q.where(
            or_(
                Actor.first_name.ilike(f"%{search}%"),
                Actor.last_name.ilike(f"%{search}%"),
            )
        )
    if ordering:
        field = ordering.lstrip("-")
        col = getattr(Actor, field, None)
        if col is not None:
            q = q.order_by(col.desc() if ordering.startswith("-") else col)
    else:
        q = q.order_by(Actor.last_name, Actor.first_name)
    return list((await db.execute(q)).scalars().all())


async def create_actor(db: AsyncSession, first_name: str, last_name: str) -> Actor:
    obj = Actor(first_name=first_name, last_name=last_name)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def update_actor(db: AsyncSession, obj: Actor, data: dict) -> Actor:
    for k, v in data.items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


async def delete_actor(db: AsyncSession, obj: Actor) -> None:
    await db.delete(obj)
    await db.commit()


# ── CinemaHall ────────────────────────────────────────────────────────────────

async def list_halls(db: AsyncSession, search: str | None, ordering: str | None) -> list[CinemaHall]:
    q = select(CinemaHall)
    if search:
        q = q.where(CinemaHall.name.ilike(f"%{search}%"))
    if ordering:
        field = ordering.lstrip("-")
        col = getattr(CinemaHall, field, None)
        if col is not None:
            q = q.order_by(col.desc() if ordering.startswith("-") else col)
    else:
        q = q.order_by(CinemaHall.name)
    return list((await db.execute(q)).scalars().all())


async def create_hall(db: AsyncSession, name: str, rows: int, seats_in_row: int) -> CinemaHall:
    obj = CinemaHall(name=name, rows=rows, seats_in_row=seats_in_row)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def update_hall(db: AsyncSession, obj: CinemaHall, data: dict) -> CinemaHall:
    for k, v in data.items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


async def delete_hall(db: AsyncSession, obj: CinemaHall) -> None:
    await db.delete(obj)
    await db.commit()


# ── Movie ─────────────────────────────────────────────────────────────────────

def _movie_query():
    return select(Movie).options(
        selectinload(Movie.genres),
        selectinload(Movie.actors),
    )


async def list_movies(
    db: AsyncSession,
    title: str | None,
    genres: list[int] | None,
    actors: list[int] | None,
    search: str | None,
    ordering: str | None,
) -> list[Movie]:
    q = _movie_query()
    if title:
        q = q.where(Movie.title.ilike(f"%{title}%"))
    if genres:
        q = q.join(Movie.genres).where(Genre.id.in_(genres))
    if actors:
        q = q.join(Movie.actors).where(Actor.id.in_(actors))
    if search:
        q = q.where(
            or_(
                Movie.title.ilike(f"%{search}%"),
                Movie.description.ilike(f"%{search}%"),
            )
        )
    if ordering:
        field = ordering.lstrip("-")
        col = getattr(Movie, field, None)
        if col is not None:
            q = q.order_by(col.desc() if ordering.startswith("-") else col)
    else:
        q = q.order_by(Movie.title)
    if genres or actors:
        q = q.distinct()
    return list((await db.execute(q)).scalars().all())


async def get_movie(db: AsyncSession, movie_id: int) -> Movie | None:
    result = await db.execute(_movie_query().where(Movie.id == movie_id))
    return result.scalar_one_or_none()


async def create_movie(
    db: AsyncSession, title: str, description: str, duration: int,
    genre_ids: list[int], actor_ids: list[int],
) -> Movie:
    genres = list((await db.execute(select(Genre).where(Genre.id.in_(genre_ids)))).scalars().all())
    actors = list((await db.execute(select(Actor).where(Actor.id.in_(actor_ids)))).scalars().all())
    obj = Movie(title=title, description=description, duration=duration, genres=genres, actors=actors)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return await get_movie(db, obj.id)  # type: ignore[return-value]


async def update_movie(db: AsyncSession, obj: Movie, data: dict[str, Any]) -> Movie:
    genre_ids = data.pop("genres", None)
    actor_ids = data.pop("actors", None)
    for k, v in data.items():
        setattr(obj, k, v)
    if genre_ids is not None:
        obj.genres = list(
            (await db.execute(select(Genre).where(Genre.id.in_(genre_ids)))).scalars().all()
        )
    if actor_ids is not None:
        obj.actors = list(
            (await db.execute(select(Actor).where(Actor.id.in_(actor_ids)))).scalars().all()
        )
    await db.commit()
    return await get_movie(db, obj.id)  # type: ignore[return-value]


async def delete_movie(db: AsyncSession, obj: Movie) -> None:
    await db.delete(obj)
    await db.commit()


async def get_recommendations(db: AsyncSession, movie: Movie) -> list[Movie]:
    genre_ids = [g.id for g in movie.genres]
    if not genre_ids:
        return []
    q = (
        _movie_query()
        .join(Movie.genres)
        .where(Genre.id.in_(genre_ids))
        .where(Movie.id != movie.id)
        .distinct()
        .limit(10)
    )
    return list((await db.execute(q)).scalars().all())


# ── MovieSession ──────────────────────────────────────────────────────────────

def _session_query():
    return select(MovieSession).options(
        selectinload(MovieSession.movie).options(
            selectinload(Movie.genres),
            selectinload(Movie.actors),
        ),
        selectinload(MovieSession.cinema_hall),
    )


async def list_sessions(
    db: AsyncSession,
    date: str | None,
    movie_id: int | None,
    ordering: str | None,
) -> list[MovieSession]:
    q = _session_query()
    if date:
        from datetime import date as date_type
        from sqlalchemy import cast, Date
        d = datetime.strptime(date, "%Y-%m-%d").date()
        q = q.where(func.date(MovieSession.show_time) == d)
    if movie_id:
        q = q.where(MovieSession.movie_id == movie_id)
    if ordering:
        field = ordering.lstrip("-")
        col = getattr(MovieSession, field, None)
        if col is not None:
            q = q.order_by(col.desc() if ordering.startswith("-") else col)
    else:
        q = q.order_by(MovieSession.show_time)
    return list((await db.execute(q)).scalars().all())


async def get_session(db: AsyncSession, session_id: int) -> MovieSession | None:
    result = await db.execute(_session_query().where(MovieSession.id == session_id))
    return result.scalar_one_or_none()


async def create_session(
    db: AsyncSession,
    movie_id: int,
    cinema_hall_id: int,
    show_time: datetime,
    price,
) -> MovieSession:
    obj = MovieSession(
        movie_id=movie_id,
        cinema_hall_id=cinema_hall_id,
        show_time=show_time,
        price=price,
    )
    db.add(obj)
    await db.commit()
    return await get_session(db, obj.id)  # type: ignore[return-value]


async def update_session(db: AsyncSession, obj: MovieSession, data: dict) -> MovieSession:
    for k, v in data.items():
        setattr(obj, k, v)
    await db.commit()
    return await get_session(db, obj.id)  # type: ignore[return-value]


async def delete_session(db: AsyncSession, obj: MovieSession) -> None:
    await db.delete(obj)
    await db.commit()


# ── Order ─────────────────────────────────────────────────────────────────────

async def list_orders(db: AsyncSession, user: User) -> list[Order]:
    q = (
        select(Order)
        .options(
            selectinload(Order.tickets).options(
                selectinload(Ticket.movie_session).options(
                    selectinload(MovieSession.movie).options(
                        selectinload(Movie.genres),
                        selectinload(Movie.actors),
                    ),
                    selectinload(MovieSession.cinema_hall),
                )
            )
        )
        .order_by(Order.created_at.desc())
    )
    if not user.is_superuser:
        q = q.where(Order.user_id == user.id)
    return list((await db.execute(q)).scalars().all())


async def create_order(db: AsyncSession, user: User, tickets_data: list[dict]) -> Order:
    """Create an order with tickets atomically. Raises ValueError on double booking."""
    now = datetime.now(timezone.utc)
    order = Order(user_id=user.id, created_at=now)
    db.add(order)
    await db.flush()  # get order.id without committing

    for t in tickets_data:
        session_id = t["movie_session"]
        row = t["row"]
        seat = t["seat"]

        # Validate seat bounds
        ms_result = await db.execute(
            _session_query().where(MovieSession.id == session_id)
        )
        ms = ms_result.scalar_one_or_none()
        if ms is None:
            raise LookupError(f"MovieSession #{session_id} not found")
        hall = ms.cinema_hall
        if not (1 <= row <= hall.rows):
            raise ValueError(f"Row must be in range 1..{hall.rows}")
        if not (1 <= seat <= hall.seats_in_row):
            raise ValueError(f"Seat must be in range 1..{hall.seats_in_row}")

        ticket = Ticket(order_id=order.id, movie_session_id=session_id, row=row, seat=seat)
        db.add(ticket)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("One of the selected seats is already taken.")

    # Re-fetch with all relations
    result = await db.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(
            selectinload(Order.tickets).options(
                selectinload(Ticket.movie_session).options(
                    selectinload(MovieSession.movie).options(
                        selectinload(Movie.genres),
                        selectinload(Movie.actors),
                    ),
                    selectinload(MovieSession.cinema_hall),
                )
            )
        )
    )
    return result.scalar_one()
