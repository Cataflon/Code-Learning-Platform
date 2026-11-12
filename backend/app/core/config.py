"""Application settings, read from environment variables and an optional .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    database_url: str = "postgresql+psycopg://autograder:autograder@localhost:5433/autograder"
    jwt_secret: str = "dev-secret-change-me-dev-secret-change-me"
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings (read once per process)."""
    return Settings()
