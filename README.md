# Online Cinema API (FastAPI)

A full-featured cinema booking REST API built with **FastAPI**, async SQLAlchemy, and JWT authentication — a direct port of the Django REST Framework portfolio project.

---

## Stack

| Concern | Library |
|---|---|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | python-jose (JWT) + passlib (bcrypt) |
| Validation | Pydantic v2 |
| Rate limiting | SlowAPI |
| Docs | Built-in OpenAPI / Swagger UI |
| Tests | pytest-asyncio + HTTPX |
| DB (prod) | PostgreSQL via asyncpg |
| DB (tests) | SQLite in-memory via aiosqlite |

---

## Features

### Authentication
| Endpoint | Method | Description |
|---|---|---|
| `/api/auth/token` | POST | Obtain access + refresh token pair |
| `/api/auth/token/refresh` | POST | Exchange refresh token for new access token |

### Catalog (admin write, public read)
| Endpoint | Description |
|---|---|
| `/api/genres` | Genre CRUD |
| `/api/actors` | Actor CRUD |
| `/api/cinema-halls` | Cinema hall CRUD |

### Movies (admin write, public read)
| Endpoint | Description |
|---|---|
| `GET /api/movies` | List with filters: `title`, `genres`, `actors`, `search`, `ordering` |
| `POST /api/movies` | Create (admin) |
| `GET /api/movies/{id}` | Detail |
| `PUT/PATCH /api/movies/{id}` | Update (admin) |
| `DELETE /api/movies/{id}` | Delete (admin) |
| `GET /api/movies/{id}/recommendations` | Up to 10 movies sharing a genre |

### Movie Sessions (admin write, public read)
| Endpoint | Description |
|---|---|
| `GET /api/movie-sessions` | List with filters: `date` (YYYY-MM-DD), `movie`, `ordering` |
| `POST /api/movie-sessions` | Create (admin) |
| `GET /api/movie-sessions/{id}` | Detail |
| `PUT/PATCH /api/movie-sessions/{id}` | Update (admin) |
| `DELETE /api/movie-sessions/{id}` | Delete (admin) |
| `GET /api/movie-sessions/{id}/available_seats` | Free seats by row |

### Orders (authentication required)
| Endpoint | Description |
|---|---|
| `GET /api/orders` | List — users see own orders, admins see all |
| `POST /api/orders` | Create order with nested tickets in one atomic request |

**Double-booking is prevented** by a `UNIQUE(movie_session_id, row, seat)` DB constraint plus an `IntegrityError` guard in the transaction layer.

### Rate limiting
- Anonymous: **10 req/min**
- Authenticated: **30 req/min**

---

## Quick start (Docker + Postgres)

### 1. Configure env
```bash
cp .env.sample .env
# Edit .env — set SECRET_KEY at minimum
```

### 2. Start services
```bash
docker compose up --build
```

### 3. Create an admin user
```bash
docker compose exec web python scripts/create_superuser.py
```

Open:
- API root: http://localhost:8000/api
- Swagger UI: http://localhost:8000/api/schema/swagger-ui
- ReDoc: http://localhost:8000/api/schema/redoc

---

## Local run (no Docker)

### 1. Create venv & install deps
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure env
```bash
cp .env.sample .env
# For local SQLite dev, set:
# DATABASE_URL=sqlite+aiosqlite:///./cinema.db
```

### 3. Run migrations
```bash
alembic upgrade head
```

### 4. Create admin
```bash
python scripts/create_superuser.py
```

### 5. Start server
```bash
uvicorn app.main:app --reload
```

---

## API usage examples

### Obtain token
```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

### Create a movie (admin)
```bash
curl -X POST http://localhost:8000/api/movies \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Interstellar",
    "description": "Space sci-fi",
    "duration": 169,
    "genres": [1, 2],
    "actors": [1]
  }'
```

### Create order with tickets
```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "tickets": [
      {"movie_session": 1, "row": 1, "seat": 1},
      {"movie_session": 1, "row": 1, "seat": 2}
    ]
  }'
```

### Filter movies
```bash
# By genre IDs (comma-separated)
curl "http://localhost:8000/api/movies?genres=1,2"

# By title + ordering
curl "http://localhost:8000/api/movies?title=inter&ordering=-duration"

# Full-text search
curl "http://localhost:8000/api/movies?search=space"
```

### Available seats
```bash
curl http://localhost:8000/api/movie-sessions/1/available_seats
```

---

## Tests

```bash
# Run all tests
pytest

# With coverage
coverage run -m pytest
coverage report -m

# Specific file
pytest tests/test_movies.py -v
```

Tests use an **in-memory SQLite** database (no Postgres required). Each test function gets a fresh, isolated DB session via `pytest-asyncio` fixtures.

---

## Project structure

This repository contains **two independent implementations** of the same cinema API:

| Directory | Stack | Requirements file |
|---|---|---|
| `app/` | FastAPI + async SQLAlchemy + Alembic | `requirements.txt` |
| `apps/` + `config/` | Django + Django REST Framework | `requirements-django.txt` |

```
online_cinema/
├── app/                          # FastAPI implementation
│   ├── main.py                   # App factory, middleware, router registration
│   ├── core/
│   │   ├── config.py             # Pydantic settings (reads .env)
│   │   ├── database.py           # Async SQLAlchemy engine + session
│   │   ├── deps.py               # FastAPI dependencies (auth, DB)
│   │   └── security.py           # JWT encode/decode, bcrypt
│   ├── models/
│   │   ├── user.py               # User model
│   │   └── cinema.py             # Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket
│   ├── schemas/
│   │   ├── auth.py               # Token request/response schemas
│   │   └── cinema.py             # All Pydantic I/O schemas + Page[T]
│   ├── crud/
│   │   └── cinema.py             # All async DB operations
│   └── routers/
│       ├── auth.py
│       ├── genres.py
│       ├── actors.py
│       ├── cinema_halls.py
│       ├── movies.py
│       ├── movie_sessions.py
│       └── orders.py
├── apps/                         # Django implementation
│   └── cinema/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── filters.py
│       ├── permissions.py
│       ├── urls.py
│       └── migrations/
├── config/                       # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── docs/                         # Project documentation
│   ├── README.md                 # Index of docs contents
│   ├── db_diagram.drawio         # Database diagram source (draw.io)
│   └── db_diagram.png            # Database diagram export
├── tests/                        # FastAPI test suite
│   ├── conftest.py               # Async fixtures, in-memory DB setup
│   ├── test_auth.py              # JWT token tests
│   ├── test_movies.py            # Movie CRUD, filters, recommendations
│   └── test_sessions_and_orders.py  # Sessions, booking, double-booking
├── scripts/
│   └── create_superuser.py       # Interactive admin user creator
├── alembic/                      # FastAPI DB migrations
│   ├── env.py                    # Async-capable Alembic environment
│   └── versions/                 # Migration files go here
├── alembic.ini
├── manage.py                     # Django management CLI
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt              # FastAPI stack dependencies
├── requirements-django.txt       # Django stack dependencies
├── .env.sample
└── .gitignore
```

---

## Django → FastAPI mapping

| Django/DRF concept | FastAPI equivalent |
|---|---|
| `ModelViewSet` | Individual `@router.get/post/patch/put/delete` endpoints |
| `IsAdminOrReadOnly` permission | `Depends(get_current_admin)` on write routes |
| `IsAuthenticated` permission | `Depends(get_current_active_user)` |
| `SimpleJWT` | `python-jose` + custom `/auth/token` router |
| `django-filter` FilterSet | Query parameters + SQLAlchemy `.where()` clauses |
| `SearchFilter` / `OrderingFilter` | Query params + `ilike` / `order_by` in CRUD layer |
| `Serializer.create()` with `transaction.atomic()` | `db.flush()` + `db.commit()` with `IntegrityError` catch |
| `drf-spectacular` Swagger | FastAPI built-in OpenAPI (zero config) |
| `AnonRateThrottle` / `UserRateThrottle` | SlowAPI `Limiter` middleware |
| `pytest-django` + `APIClient` | `pytest-asyncio` + `httpx.AsyncClient` |
| `manage.py migrate` | `alembic upgrade head` |
| `manage.py createsuperuser` | `python scripts/create_superuser.py` |
