from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.crud.cinema import (
    create_session,
    delete_session,
    get_session,
    list_sessions,
    update_session,
)
from app.models.cinema import Ticket
from app.models.user import User
from app.schemas.cinema import (
    AvailableSeatsOut,
    MovieSessionCreate,
    MovieSessionOut,
    MovieSessionUpdate,
    Page,
    RowAvailability,
)

router = APIRouter(prefix="/movie-sessions", tags=["Movie sessions"])


@router.get("", response_model=Page[MovieSessionOut])
async def read_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    date: str | None = Query(None, description="Filter by date YYYY-MM-DD"),
    movie: int | None = Query(None, description="Filter by movie ID"),
    ordering: str | None = Query(None, description="Order by show_time or price. Example: -show_time"),
):
    items = await list_sessions(db, date, movie, ordering)
    return Page(count=len(items), results=items)


@router.post("", response_model=MovieSessionOut, status_code=status.HTTP_201_CREATED)
async def create_session_view(
    body: MovieSessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    return await create_session(db, body.movie_id, body.cinema_hall_id, body.show_time, body.price)


@router.get("/{session_id}", response_model=MovieSessionOut)
async def read_session(session_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    session = await get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"MovieSession #{session_id} not found")
    return session


@router.patch("/{session_id}", response_model=MovieSessionOut)
async def update_session_view(
    session_id: int,
    body: MovieSessionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    session = await get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"MovieSession #{session_id} not found")
    return await update_session(db, session, body.model_dump(exclude_unset=True))


@router.put("/{session_id}", response_model=MovieSessionOut)
async def replace_session(
    session_id: int,
    body: MovieSessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    session = await get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"MovieSession #{session_id} not found")
    return await update_session(db, session, body.model_dump())


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_view(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    session = await get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"MovieSession #{session_id} not found")
    await delete_session(db, session)


@router.get(
    "/{session_id}/available_seats",
    response_model=AvailableSeatsOut,
    summary="Return available (not yet booked) seats for a session",
)
async def available_seats(session_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    session = await get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"MovieSession #{session_id} not found")

    hall = session.cinema_hall
    result = await db.execute(
        select(Ticket.row, Ticket.seat).where(Ticket.movie_session_id == session_id)
    )
    taken = set(result.all())

    available = []
    for r in range(1, hall.rows + 1):
        free = [s for s in range(1, hall.seats_in_row + 1) if (r, s) not in taken]
        if free:
            available.append(RowAvailability(row=r, seats=free))

    return AvailableSeatsOut(session_id=session.id, hall=hall.name, available=available)
