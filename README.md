# Online Cinema API (Portfolio Project)

Cinema-style Django REST Framework project with:

- JWT authentication (SimpleJWT)
- Swagger/OpenAPI documentation (drf-spectacular)
- Throttling: **10 req/min** for anonymous, **30 req/min** for authenticated users
- Filtering + Search + Ordering
- Custom endpoints (actions) documented in Swagger
- Tests (pytest + coverage)
- Docker + Postgres
- DB diagram (`docs/db_diagram.drawio` + exported `docs/db_diagram.png`)

---

## Features

### Authentication
- Obtain token: `POST /api/auth/token/`
- Refresh token: `POST /api/auth/token/refresh/`

### Catalog
- Genres CRUD: `/api/genres/` (admin write, public read)
- Actors CRUD: `/api/actors/` (admin write, public read)

### Cinema
- Cinema halls CRUD: `/api/cinema-halls/` (admin write, public read)
- Movies CRUD: `/api/movies/` (admin write, public read)
  - Filters: `title`, `genres`, `actors`
  - Search: `search` (title/description)
  - Ordering: `ordering` (title, duration)
  - Custom action: `GET /api/movies/{id}/recommendations/`
- Movie sessions CRUD: `/api/movie-sessions/` (admin write, public read)
  - Filters: `date`, `movie`
  - Ordering: `ordering` (show_time, price)
  - Custom action: `GET /api/movie-sessions/{id}/available_seats/`

### Orders
- Orders list/create: `/api/orders/` (auth required)
  - Users see only their orders, admins see all
  - Create order with nested tickets in one request
  - Seats cannot be double-booked (DB constraint + validation)

---

## Quick start (Docker + Postgres)

### 1) Configure env
```bash
cp .env.sample .env
```

### 2) Run
```bash
docker compose up --build
```

### 3) Apply migrations and create admin
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Open:
- API root: http://127.0.0.1:8000/api/
- Swagger UI: http://127.0.0.1:8000/api/schema/swagger-ui/

---

## Local run (no Docker)

### 1) Create venv & install deps
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Env
```bash
cp .env.sample .env
```

### 3) Migrations
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4) Run server
```bash
python manage.py runserver
```

---

## How to use (examples)

### Get JWT token
```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

### Create a movie (admin)
```bash
curl -X POST http://127.0.0.1:8000/api/movies/ \
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

### Create order with tickets (auth user)
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "tickets": [
      {"movie_session": 1, "row": 1, "seat": 1},
      {"movie_session": 1, "row": 1, "seat": 2}
    ]
  }'
```

---

## Tests + coverage
```bash
coverage run -m pytest
coverage report -m
```

---

## DB Diagram
- Source: `docs/db_diagram.drawio`
- Export: `docs/db_diagram.png`

---

## Suggested Git workflow (for Mate Academy requirements)
- Work in feature branches:
  - `feature/auth-jwt`
  - `feature/movies-crud-filters`
  - `feature/sessions-custom-actions`
  - `feature/orders-tickets`
- Open PRs into `develop`
- Final PR: `develop -> main`
- Use proper commit names per task (see `CONTRIBUTING.md`)
