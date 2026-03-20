from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.crud.cinema import (
    create_movie,
    delete_movie,
    get_movie,
    get_recommendations,
    list_movies,
    update_movie,
)
from app.models.user import User
from app.schemas.cinema import (
    MovieCreate,
    MovieDetailOut,
    MovieListOut,
    MovieUpdate,
    Page,
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("", response_model=Page[MovieListOut])
async def read_movies(
    db: Annotated[AsyncSession, Depends(get_db)],
    title: str | None = Query(None, description="Filter by title (case-insensitive contains)"),
    genres: str | None = Query(None, description="Comma-separated genre IDs. Example: 1,2"),
    actors: str | None = Query(None, description="Comma-separated actor IDs. Example: 1,5"),
    search: str | None = Query(None, description="Search in title and description"),
    ordering: str | None = Query(None, description="Order by field. Prefix with - for descending. Example: -duration"),
):
    genre_ids = [int(x) for x in genres.split(",") if x.strip()] if genres else None
    actor_ids = [int(x) for x in actors.split(",") if x.strip()] if actors else None
    items = await list_movies(db, title, genre_ids, actor_ids, search, ordering)
    return Page(count=len(items), results=items)


@router.post("", response_model=MovieDetailOut, status_code=status.HTTP_201_CREATED)
async def create_movie_view(
    body: MovieCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    return await create_movie(db, body.title, body.description, body.duration, body.genres, body.actors)


@router.get("/{movie_id}", response_model=MovieDetailOut)
async def read_movie(movie_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    movie = await get_movie(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=f"Movie #{movie_id} not found")
    return movie


@router.patch("/{movie_id}", response_model=MovieDetailOut)
async def update_movie_view(
    movie_id: int,
    body: MovieUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    movie = await get_movie(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=f"Movie #{movie_id} not found")
    return await update_movie(db, movie, body.model_dump(exclude_unset=True))


@router.put("/{movie_id}", response_model=MovieDetailOut)
async def replace_movie(
    movie_id: int,
    body: MovieCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    movie = await get_movie(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=f"Movie #{movie_id} not found")
    return await update_movie(db, movie, body.model_dump())


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie_view(
    movie_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    movie = await get_movie(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=f"Movie #{movie_id} not found")
    await delete_movie(db, movie)


@router.get(
    "/{movie_id}/recommendations",
    response_model=list[MovieListOut],
    summary="Movies sharing at least one genre with the given movie (up to 10)",
)
async def recommendations(movie_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    movie = await get_movie(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=f"Movie #{movie_id} not found")
    return await get_recommendations(db, movie)
