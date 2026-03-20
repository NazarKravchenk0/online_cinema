from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_active_user
from app.crud.cinema import create_genre, delete_genre, get_or_404, list_genres, update_genre
from app.models.cinema import Genre
from app.models.user import User
from app.schemas.cinema import GenreCreate, GenreOut, GenreUpdate, Page

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("", response_model=Page[GenreOut])
async def read_genres(
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(None),
    ordering: str | None = Query(None),
):
    items = await list_genres(db, search, ordering)
    return Page(count=len(items), results=items)


@router.post("", response_model=GenreOut, status_code=status.HTTP_201_CREATED)
async def create_genre_view(
    body: GenreCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    return await create_genre(db, body.name)


@router.get("/{genre_id}", response_model=GenreOut)
async def read_genre(genre_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await get_or_404(db, Genre, genre_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{genre_id}", response_model=GenreOut)
async def update_genre_view(
    genre_id: int,
    body: GenreUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    try:
        obj = await get_or_404(db, Genre, genre_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    data = body.model_dump(exclude_unset=True)
    return await update_genre(db, obj, data)


@router.put("/{genre_id}", response_model=GenreOut)
async def replace_genre(
    genre_id: int,
    body: GenreCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    try:
        obj = await get_or_404(db, Genre, genre_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return await update_genre(db, obj, body.model_dump())


@router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_genre_view(
    genre_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    try:
        obj = await get_or_404(db, Genre, genre_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await delete_genre(db, obj)
