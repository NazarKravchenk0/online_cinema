from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    class Meta:
        ordering = ("last_name", "first_name")
        unique_together = ("first_name", "last_name")

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class CinemaHall(models.Model):
    name = models.CharField(max_length=255, unique=True)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()

    class Meta:
        ordering = ("name",)

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self) -> str:
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    actors = models.ManyToManyField(Actor, related_name="movies", blank=True)

    class Meta:
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title


class MovieSession(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="sessions")
    cinema_hall = models.ForeignKey(CinemaHall, on_delete=models.PROTECT, related_name="sessions")
    show_time = models.DateTimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ("show_time",)
        indexes = [
            models.Index(fields=["show_time"]),
            models.Index(fields=["movie", "show_time"]),
        ]

    def clean(self) -> None:
        if not self.movie_id or not self.cinema_hall_id or not self.show_time:
            return

        start = self.show_time
        end = self.show_time + timedelta(minutes=self.movie.duration)

        qs = MovieSession.objects.filter(cinema_hall_id=self.cinema_hall_id).select_related("movie")
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        for s in qs:
            s_start = s.show_time
            s_end = s.show_time + timedelta(minutes=s.movie.duration)
            if s_start < end and s_end > start:
                raise ValidationError("Movie session overlaps with an existing session in the same hall.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.movie.title} @ {self.show_time}"


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Order #{self.id}"


class Ticket(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")
    movie_session = models.ForeignKey(MovieSession, on_delete=models.CASCADE, related_name="tickets")
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()

    class Meta:
        unique_together = ("movie_session", "row", "seat")
        ordering = ("movie_session", "row", "seat")

    def clean(self) -> None:
        hall = self.movie_session.cinema_hall if self.movie_session_id else None
        if hall:
            if not (1 <= self.row <= hall.rows):
                raise ValidationError({"row": f"Row must be in range 1..{hall.rows}"})
            if not (1 <= self.seat <= hall.seats_in_row):
                raise ValidationError({"seat": f"Seat must be in range 1..{hall.seats_in_row}"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Ticket session={self.movie_session_id} r{self.row}s{self.seat}"
