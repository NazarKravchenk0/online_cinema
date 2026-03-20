from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import actors, auth, cinema_halls, genres, movie_sessions, movies, orders


def _get_rate_limit_key(request: Request) -> str:
    """Use user id when authenticated, otherwise remote IP."""
    token = request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        # Authenticated – use the token as key so the user-rate applies.
        # SlowAPI still applies the limit string we choose per decorator.
        return f"user:{token[7:30]}"
    return get_remote_address(request)


limiter = Limiter(key_func=_get_rate_limit_key, default_limits=[settings.ANON_RATE_LIMIT])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_TITLE,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        docs_url="/api/schema/swagger-ui",
        redoc_url="/api/schema/redoc",
        openapi_url="/api/schema",
        lifespan=lifespan,
    )

    # ── Rate limiting ────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────────────
    prefix = "/api"
    app.include_router(auth.router, prefix=prefix)
    app.include_router(genres.router, prefix=prefix)
    app.include_router(actors.router, prefix=prefix)
    app.include_router(cinema_halls.router, prefix=prefix)
    app.include_router(movies.router, prefix=prefix)
    app.include_router(movie_sessions.router, prefix=prefix)
    app.include_router(orders.router, prefix=prefix)

    @app.get("/api", tags=["Root"], summary="API root")
    async def api_root():
        return {
            "genres": "/api/genres/",
            "actors": "/api/actors/",
            "cinema-halls": "/api/cinema-halls/",
            "movies": "/api/movies/",
            "movie-sessions": "/api/movie-sessions/",
            "orders": "/api/orders/",
            "auth": {
                "token": "/api/auth/token",
                "refresh": "/api/auth/token/refresh",
            },
            "docs": "/api/schema/swagger-ui",
        }

    return app


app = create_app()
