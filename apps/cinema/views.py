from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import MovieFilter, MovieSessionFilter
from .models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket
from .permissions import IsAdminOrReadOnly
from .serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieListSerializer,
    MovieDetailSerializer,
    MovieCreateUpdateSerializer,
    MovieSessionListSerializer,
    MovieSessionCreateUpdateSerializer,
    OrderListSerializer,
    OrderCreateSerializer,
)


@extend_schema(tags=["Genres"])
class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    search_fields = ("name",)
    ordering_fields = ("name",)


@extend_schema(tags=["Actors"])
class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = (IsAdminOrReadOnly,)
    search_fields = ("first_name", "last_name")
    ordering_fields = ("last_name", "first_name")


@extend_schema(tags=["Cinema halls"])
class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    permission_classes = (IsAdminOrReadOnly,)
    search_fields = ("name",)
    ordering_fields = ("name", "rows", "seats_in_row")


@extend_schema(
    tags=["Movies"],
    parameters=[
        OpenApiParameter(name="title", description="Filter by title (icontains).", required=False, type=str),
        OpenApiParameter(
            name="genres",
            description="Filter by genre ids (comma-separated). Example: 1,2",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="actors",
            description="Filter by actor ids (comma-separated). Example: 1,5",
            required=False,
            type=str,
        ),
        OpenApiParameter(name="search", description="Search in title/description.", required=False, type=str),
        OpenApiParameter(name="ordering", description="Order by title or duration. Example: -duration", required=False, type=str),
    ],
)
class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "actors").all()
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = MovieFilter
    search_fields = ("title", "description")
    ordering_fields = ("title", "duration")

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieCreateUpdateSerializer

    @extend_schema(description="Recommendations: movies sharing at least one genre with current movie.")
    @action(detail=True, methods=["get"])
    def recommendations(self, request, pk=None):
        movie = self.get_object()
        genre_ids = movie.genres.values_list("id", flat=True)
        qs = (
            Movie.objects.prefetch_related("genres", "actors")
            .filter(genres__in=genre_ids)
            .exclude(id=movie.id)
            .distinct()[:10]
        )
        serializer = MovieListSerializer(qs, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=["Movie sessions"],
    parameters=[
        OpenApiParameter(name="date", description="Filter by date YYYY-MM-DD.", required=False, type=str),
        OpenApiParameter(name="movie", description="Filter by movie id.", required=False, type=int),
        OpenApiParameter(name="ordering", description="Order by show_time or price. Example: -show_time", required=False, type=str),
    ],
)
class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related("movie", "cinema_hall").all()
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = MovieSessionFilter
    ordering_fields = ("show_time", "price")

    def get_serializer_class(self):
        if self.action in ("list", "retrieve", "available_seats"):
            return MovieSessionListSerializer
        return MovieSessionCreateUpdateSerializer

    @extend_schema(description="Return available seats for the session (rows with free seats).")
    @action(detail=True, methods=["get"], url_path="available_seats")
    def available_seats(self, request, pk=None):
        session = self.get_object()
        hall = session.cinema_hall
        taken = set(Ticket.objects.filter(movie_session=session).values_list("row", "seat"))
        available = []
        for r in range(1, hall.rows + 1):
            free_seats = [s for s in range(1, hall.seats_in_row + 1) if (r, s) not in taken]
            if free_seats:
                available.append({"row": r, "seats": free_seats})
        return Response({"session_id": session.id, "hall": hall.name, "available": available})


@extend_schema(tags=["Orders"])
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets__movie_session__movie",
        "tickets__movie_session__cinema_hall",
    ).all()
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff:
            return qs
        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderListSerializer
        return OrderCreateSerializer
