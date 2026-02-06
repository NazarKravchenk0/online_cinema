from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Actor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=255)),
                ("last_name", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ("last_name", "first_name"),
                "unique_together": {("first_name", "last_name")},
            },
        ),
        migrations.CreateModel(
            name="CinemaHall",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("rows", models.PositiveIntegerField()),
                ("seats_in_row", models.PositiveIntegerField()),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="Genre",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="Movie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                ("duration", models.PositiveIntegerField(help_text="Duration in minutes")),
                ("actors", models.ManyToManyField(blank=True, related_name="movies", to="cinema.actor")),
                ("genres", models.ManyToManyField(blank=True, related_name="movies", to="cinema.genre")),
            ],
            options={"ordering": ("title",)},
        ),
        migrations.CreateModel(
            name="MovieSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("show_time", models.DateTimeField()),
                ("price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("cinema_hall", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessions", to="cinema.cinemahall")),
                ("movie", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sessions", to="cinema.movie")),
            ],
            options={"ordering": ("show_time",)},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("row", models.PositiveIntegerField()),
                ("seat", models.PositiveIntegerField()),
                ("movie_session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tickets", to="cinema.moviesession")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tickets", to="cinema.order")),
            ],
            options={
                "ordering": ("movie_session", "row", "seat"),
                "unique_together": {("movie_session", "row", "seat")},
            },
        ),
        migrations.AddIndex(
            model_name="moviesession",
            index=models.Index(fields=["show_time"], name="cinema_mov_show_t_0d92a8_idx"),
        ),
        migrations.AddIndex(
            model_name="moviesession",
            index=models.Index(fields=["movie", "show_time"], name="cinema_mov_movie_i_6bc3b3_idx"),
        ),
    ]
