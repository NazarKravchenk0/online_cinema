from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator

T = TypeVar("T")


# ── Pagination ───────────────────────────────────────────────────────────────

class Page(BaseModel, Generic[T]):
    count: int
    results: list[T]


# ── Genre ────────────────────────────────────────────────────────────────────

class GenreBase(BaseModel):
    name: str


class GenreCreate(GenreBase):
    pass


class GenreUpdate(BaseModel):
    name: str | None = None


class GenreOut(GenreBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── Actor ────────────────────────────────────────────────────────────────────

class ActorBase(BaseModel):
    first_name: str
    last_name: str


class ActorCreate(ActorBase):
    pass


class ActorUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None


class ActorOut(ActorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── CinemaHall ───────────────────────────────────────────────────────────────

class CinemaHallBase(BaseModel):
    name: str
    rows: int
    seats_in_row: int


class CinemaHallCreate(CinemaHallBase):
    pass


class CinemaHallUpdate(BaseModel):
    name: str | None = None
    rows: int | None = None
    seats_in_row: int | None = None


class CinemaHallOut(CinemaHallBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    capacity: int


# ── Movie ────────────────────────────────────────────────────────────────────

class MovieCreate(BaseModel):
    title: str
    description: str = ""
    duration: int
    genres: list[int] = []
    actors: list[int] = []


class MovieUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    duration: int | None = None
    genres: list[int] | None = None
    actors: list[int] | None = None


class MovieListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    duration: int
    genres: list[GenreOut]
    actors: list[ActorOut]


class MovieDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    duration: int
    genres: list[GenreOut]
    actors: list[ActorOut]


# ── MovieSession ──────────────────────────────────────────────────────────────

class MovieSessionCreate(BaseModel):
    movie_id: int
    cinema_hall_id: int
    show_time: datetime
    price: Decimal


class MovieSessionUpdate(BaseModel):
    movie_id: int | None = None
    cinema_hall_id: int | None = None
    show_time: datetime | None = None
    price: Decimal | None = None


class MovieSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    movie: MovieListOut
    cinema_hall: CinemaHallOut
    show_time: datetime
    price: Decimal


# ── Available seats ───────────────────────────────────────────────────────────

class RowAvailability(BaseModel):
    row: int
    seats: list[int]


class AvailableSeatsOut(BaseModel):
    session_id: int
    hall: str
    available: list[RowAvailability]


# ── Ticket ────────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    movie_session: int  # session id
    row: int
    seat: int

    @field_validator("row", "seat")
    @classmethod
    def positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Must be >= 1")
        return v


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    movie_session: MovieSessionOut
    row: int
    seat: int


# ── Order ────────────────────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    tickets: list[TicketCreate]


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    tickets: list[TicketOut]
