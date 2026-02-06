import django_filters
from django.utils.dateparse import parse_date

from .models import Movie, MovieSession

class MovieFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    genres = django_filters.BaseInFilter(field_name="genres__id", lookup_expr="in")
    actors = django_filters.BaseInFilter(field_name="actors__id", lookup_expr="in")

    class Meta:
        model = Movie
        fields = ("title", "genres", "actors")


class MovieSessionFilter(django_filters.FilterSet):
    date = django_filters.CharFilter(method="filter_date")
    movie = django_filters.NumberFilter(field_name="movie_id")

    class Meta:
        model = MovieSession
        fields = ("date", "movie")

    def filter_date(self, queryset, name, value):
        dt = parse_date(value)
        if not dt:
            return queryset
        return queryset.filter(show_time__date=dt)
