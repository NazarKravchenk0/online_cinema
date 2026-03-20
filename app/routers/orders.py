from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.crud.cinema import create_order, list_orders
from app.models.user import User
from app.schemas.cinema import OrderCreate, OrderOut, Page

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=Page[OrderOut])
async def read_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """List orders. Regular users see only their own; admins see all."""
    items = await list_orders(db, current_user)
    return Page(count=len(items), results=items)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order_view(
    body: OrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Create an order with one or more tickets in a single atomic transaction."""
    if not body.tickets:
        raise HTTPException(status_code=400, detail="At least one ticket is required.")
    tickets_data = [t.model_dump() for t in body.tickets]
    try:
        return await create_order(db, current_user, tickets_data)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
