from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.crud.cinema import create_actor, delete_actor, get_or_404, list_actors, update_actor
from app.models.cinema import Actor
from app.models.user import User
from app.schemas.cinema import ActorCreate, ActorOut, ActorUpdate, Page

router = APIRouter(prefix="/actors", tags=["Actors"])


@router.get("", response_model=Page[ActorOut])
async def read_actors(
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(None),
    ordering: str | None = Query(None),
):
    items = await list_actors(db, search, ordering)
    return Page(count=len(items), results=items)


@router.post("", response_model=ActorOut, status_code=status.HTTP_201_CREATED)
async def create_actor_view(
    body: ActorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    return await create_actor(db, body.first_name, body.last_name)


@router.get("/{actor_id}", response_model=ActorOut)
async def read_actor(actor_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await get_or_404(db, Actor, actor_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{actor_id}", response_model=ActorOut)
async def update_actor_view(
    actor_id: int,
    body: ActorUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    try:
        obj = await get_or_404(db, Actor, actor_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return await update_actor(db, obj, body.model_dump(exclude_unset=True))


@router.put("/{actor_id}", response_model=ActorOut)
async def replace_actor(
    actor_id: int,
    body: ActorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    try:
        obj = await get_or_404(db, Actor, actor_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return await update_actor(db, obj, body.model_dump())


@router.delete("/{actor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_actor_view(
    actor_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
):
    try:
        obj = await get_or_404(db, Actor, actor_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await delete_actor(db, obj)
