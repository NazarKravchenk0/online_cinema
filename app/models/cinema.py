from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# ── Association tables ──────────────────────────────────────────────────────

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

movie_actors = Table(
    "movie_actors",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("actor_id", Integer, ForeignKey("actors.id", ondelete="CASCADE"), primary_key=True),
)


# ── Core models ─────────────────────────────────────────────────────────────

class Genre(Base):
    __tablename__ = "genres"
    __table_args__ = (UniqueConstraint("name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary=movie_genres, back_populates="genres"
    )


class Actor(Base):
    __tablename__ = "actors"
    __table_args__ = (UniqueConstraint("first_name", "last_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary=movie_actors, back_populates="actors"
    )


class CinemaHall(Base):
    __tablename__ = "cinema_halls"
    __table_args__ = (UniqueConstraint("name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rows: Mapped[int] = mapped_column(Integer, nullable=False)
    seats_in_row: Mapped[int] = mapped_column(Integer, nullable=False)

    sessions: Mapped[list["MovieSession"]] = relationship("MovieSession", back_populates="cinema_hall")

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (UniqueConstraint("title"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    duration: Mapped[int] = mapped_column(Integer, nullable=False)  # minutes

    genres: Mapped[list[Genre]] = relationship(
        Genre, secondary=movie_genres, back_populates="movies", lazy="selectin"
    )
    actors: Mapped[list[Actor]] = relationship(
        Actor, secondary=movie_actors, back_populates="movies", lazy="selectin"
    )
    sessions: Mapped[list["MovieSession"]] = relationship("MovieSession", back_populates="movie")


class MovieSession(Base):
    __tablename__ = "movie_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    cinema_hall_id: Mapped[int] = mapped_column(
        ForeignKey("cinema_halls.id", ondelete="RESTRICT"), nullable=False
    )
    show_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    movie: Mapped[Movie] = relationship(Movie, back_populates="sessions", lazy="selectin")
    cinema_hall: Mapped[CinemaHall] = relationship(CinemaHall, back_populates="sessions", lazy="selectin")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="movie_session")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="orders")  # noqa: F821
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="order", lazy="selectin"
    )


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("movie_session_id", "row", "seat", name="uq_ticket_seat"),
        CheckConstraint("row >= 1", name="ck_ticket_row_min"),
        CheckConstraint("seat >= 1", name="ck_ticket_seat_min"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    movie_session_id: Mapped[int] = mapped_column(
        ForeignKey("movie_sessions.id", ondelete="CASCADE"), nullable=False
    )
    row: Mapped[int] = mapped_column(Integer, nullable=False)
    seat: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped[Order] = relationship(Order, back_populates="tickets")
    movie_session: Mapped[MovieSession] = relationship(
        MovieSession, back_populates="tickets", lazy="selectin"
    )
