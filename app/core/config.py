from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./cinema.db"

    # JWT
    SECRET_KEY: str = "unsafe-dev-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Throttle (requests per minute)
    ANON_RATE_LIMIT: str = "10/minute"
    USER_RATE_LIMIT: str = "30/minute"

    # App
    DEBUG: bool = True
    PROJECT_TITLE: str = "Online Cinema API"
    PROJECT_DESCRIPTION: str = "Portfolio Online Cinema API (FastAPI)."
    PROJECT_VERSION: str = "1.0.0"


settings = Settings()
