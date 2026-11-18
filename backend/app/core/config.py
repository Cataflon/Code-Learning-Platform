"""Application settings, read from environment variables and an optional .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


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

    # Concept report levels (Step 7): below the first is "review", from the second "mastered".
    concept_review_below: float = 0.5
    concept_mastered_from: float = 0.8

    # Course materials (Step 8)
    upload_dir: Path = REPO_ROOT / "uploads"
    max_upload_mb: int = 20
    pptx_convert_timeout_s: int = 60
    # Path to LibreOffice's soffice; empty = look in PATH and in the usual install folders.
    soffice_path: str = ""

    # AI test generation (Step 9, decisions D25-D29). Optional: without a key it is off.
    # Default provider: the NVIDIA API catalog (OpenAI-compatible); Claude stays an option.
    ai_enabled: bool = True
    ai_provider: Literal["nvidia", "anthropic"] = "nvidia"
    nvidia_api_key: SecretStr = SecretStr("")  # never logged, never returned
    anthropic_api_key: SecretStr = SecretStr("")
    ai_base_url: str = "https://integrate.api.nvidia.com/v1"
    ai_model: str = "nvidia/nemotron-3-ultra-550b-a55b"
    ai_effort: Literal["low", "medium", "high", "xhigh", "max"] = "high"  # Claude only
    ai_timeout_s: int = 120
    ai_max_jobs_per_hour: int = 5

    @property
    def ai_api_key(self) -> SecretStr:
        """The key of the selected provider."""
        return self.nvidia_api_key if self.ai_provider == "nvidia" else self.anthropic_api_key

    @property
    def ai_available(self) -> bool:
        return self.ai_enabled and bool(self.ai_api_key.get_secret_value().strip())

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
