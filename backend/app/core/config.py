"""Application settings, read from environment variables and an optional .env file."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    database_url: str = "postgresql+psycopg://autograder:autograder@localhost:5433/autograder"
    jwt_secret: str = "dev-secret-change-me-dev-secret-change-me"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Authentication
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    # Registering as a teacher requires this code (decision D5).
    teacher_invite_code: str = "PROF-2026"

    # Code execution (decision D12 for the defaults)
    runner: Literal["docker", "subprocess"] = "docker"
    sandbox_image: str = "autograder-python:latest"
    sandbox_cpus: float = 0.5
    sandbox_pids_limit: int = 64
    sandbox_startup_margin_ms: int = 2000
    max_concurrent_runs: int = 2
    # Minimum time between two submissions of one student to one assignment (else 429).
    min_submission_interval_s: int = 5

    @model_validator(mode="after")
    def _subprocess_runner_only_in_dev(self) -> Self:
        # SubprocessRunner is not a sandbox: refuse to start with it anywhere but dev.
        if self.runner == "subprocess" and self.env != "dev":
            raise ValueError("RUNNER=subprocess is only allowed when ENV=dev")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings (read once per process)."""
    return Settings()
