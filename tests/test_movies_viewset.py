import pytest
from apps.cinema.models import Movie, Genre, Actor

pytestmark = pytest.mark.django_db

def test_movies_list_public(api_client, movie):
    res = api_client.get("/api/movies/")
    assert res.status_code == 200
    assert res.data["count"] == 1

def test_movies_retrieve_public(api_client, movie):
    res = api_client.get(f"/api/movies/{movie.id}/")
    assert res.status_code == 200
    assert res.data["title"] == movie.title

def test_movies_create_requires_admin(api_client, genre_action, actor_one):
    payload = {
        "title": "New Movie",
        "description": "",
        "duration": 90,
        "genres": [genre_action.id],
        "actors": [actor_one.id],
    }
    res = api_client.post("/api/movies/", payload, format="json")
    assert res.status_code in (401, 403)

def test_movies_create_admin_success(api_client, admin_user, genre_action, actor_one):
    api_client.force_authenticate(user=admin_user)
    payload = {
        "title": "New Movie",
        "description": "D",
        "duration": 90,
        "genres": [genre_action.id],
        "actors": [actor_one.id],
    }
    res = api_client.post("/api/movies/", payload, format="json")
    assert res.status_code == 201
    assert Movie.objects.filter(title="New Movie").exists()

def test_movies_update_admin(api_client, admin_user, movie):
    api_client.force_authenticate(user=admin_user)
    res = api_client.patch(f"/api/movies/{movie.id}/", {"duration": 130}, format="json")
    assert res.status_code == 200
    movie.refresh_from_db()
    assert movie.duration == 130

def test_movies_delete_admin(api_client, admin_user, movie):
    api_client.force_authenticate(user=admin_user)
    res = api_client.delete(f"/api/movies/{movie.id}/")
    assert res.status_code == 204
    assert Movie.objects.count() == 0

def test_movies_filter_by_title(api_client, movie):
    res = api_client.get("/api/movies/?title=Movie")
    assert res.status_code == 200
    assert res.data["count"] == 1

def test_movies_filter_by_genres(api_client, genre_action):
    g2 = Genre.objects.create(name="Drama")
    a2 = Actor.objects.create(first_name="Amy", last_name="Adams")
    m2 = Movie.objects.create(title="Movie B", description="", duration=100)
    m2.genres.add(g2)
    m2.actors.add(a2)

    res = api_client.get(f"/api/movies/?genres={genre_action.id}")
    assert res.status_code == 200
    assert res.data["count"] == 1

def test_movies_filter_by_actors(api_client, actor_one):
    res = api_client.get(f"/api/movies/?actors={actor_one.id}")
    assert res.status_code == 200
    assert res.data["count"] == 1

def test_movies_search(api_client, movie):
    res = api_client.get("/api/movies/?search=Desc")
    assert res.status_code == 200
    assert res.data["count"] == 1

def test_movies_ordering(api_client, movie):
    Movie.objects.create(title="AAA", description="", duration=50)
    res = api_client.get("/api/movies/?ordering=title")
    assert res.status_code == 200
    assert res.data["results"][0]["title"] == "AAA"

def test_movies_recommendations(api_client, movie):
    m2 = Movie.objects.create(title="Movie C", description="", duration=110)
    m2.genres.set(movie.genres.all())
    res = api_client.get(f"/api/movies/{movie.id}/recommendations/")
    assert res.status_code == 200
    assert isinstance(res.data, list)
