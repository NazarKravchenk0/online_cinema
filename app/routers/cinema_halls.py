from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.crud.cinema import create_hall, delete_hall, get_or_404, list_halls, update_hall
from app.models.cinema import CinemaHall
from app.models.user import User
from app.schemas.cinema import CinemaHallCreate, CinemaHallOut, CinemaHallUpdate, Page

router = APIRouter(prefix="/cinema-halls", tags=["Cinema halls"])


@router.get("", response_model=Page[CinemaHallOut])
async def read_halls(
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(None),
    ordering: str | None = Query(None),
):
    items = await list_halls(db, search, ordering)
    return Page(count=len(items), results=items)


@router.post("", response_model=CinemaHallOut, status_code=status.HTTP_201_CREATED)
async def create_hall_view(
    body: CinemaHallCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    return await create_hall(db, body.name, body.rows, body.seats_in_row)


@router.get("/{hall_id}", response_model=CinemaHallOut)
async def read_hall(hall_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await get_or_404(db, CinemaHall, hall_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{hall_id}", response_model=CinemaHallOut)
async def update_hall_view(
    hall_id: int,
    body: CinemaHallUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    try:
        obj = await get_or_404(db, CinemaHall, hall_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return await update_hall(db, obj, body.model_dump(exclude_unset=True))


@router.put("/{hall_id}", response_model=CinemaHallOut)
async def replace_hall(
    hall_id: int,
    body: CinemaHallCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    try:
        obj = await get_or_404(db, CinemaHall, hall_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return await update_hall(db, obj, body.model_dump())


@router.delete("/{hall_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hall_view(
    hall_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    try:
        obj = await get_or_404(db, CinemaHall, hall_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await delete_hall(db, obj)
