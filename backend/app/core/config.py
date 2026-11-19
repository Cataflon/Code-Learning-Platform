"""Application settings, read from environment variables and an optional .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]

# Defaults per AI provider (decision D25, revised 18.11.2026). Gemini's free tier often answers
# 503 "high demand" for one model while another works, hence the fallbacks.
AI_PROVIDER_DEFAULTS: dict[str, dict] = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3.5-flash",
        "fallbacks": ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite"),
        "timeout_s": 45,
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "nvidia/nemotron-3-ultra-550b-a55b",
        "fallbacks": (),
        "timeout_s": 120,
    },
    "anthropic": {
        "base_url": "",
        "model": "claude-sonnet-5-5",
        "fallbacks": (),
        "timeout_s": 120,
    },
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    database_url: str = "postgresql+psycopg://autograder:autograder@localhost:5433/autograder"
    jwt_secret: str = "dev-secret-change-me-dev-secret-change-me"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Authentication
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    # Registering as a teacher requires an invite code made by an admin (D30). This code from
    # the settings is also accepted, so a new install has a way in; empty = only admin codes.
    teacher_invite_code: str = "PROF-2026"

    # Code execution (decision D12 for the defaults)
    runner: Literal["docker", "subprocess"] = "docker"
    sandbox_image: str = "autograder-python:latest"
    sandbox_cpus: float = 0.5
    sandbox_pids_limit: int = 64
    sandbox_startup_margin_ms: int = 2000
    max_concurrent_runs: int = 2
    # Where the runner writes main.py and input.txt before mounting them in the sandbox.
    # Empty = the system temp folder. When the backend itself runs in a container (compose
    # profile "demo"), this folder must exist at the same path on the Docker host.
    sandbox_work_dir: str = ""
    # Minimum time between two submissions of one student to one assignment (else 429).
    min_submission_interval_s: int = 5

    # Logging and abuse limits (Step 10)
    log_level: str = "INFO"
    rate_limit_enabled: bool = True
    rate_limit_login_per_minute: int = 10  # sign-in and registration, per IP address
    rate_limit_submissions_per_minute: int = 20  # per student, across assignments
    rate_limit_uploads_per_10_minutes: int = 20  # material uploads, per teacher

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
    # Default provider: Gemini (Google AI Studio) through its OpenAI-compatible endpoint; the
    # NVIDIA API catalog and Claude stay options. Empty model / URL / timeout = provider default.
    ai_enabled: bool = True
    ai_provider: Literal["gemini", "nvidia", "anthropic"] = "gemini"
    gemini_api_key: SecretStr = SecretStr("")  # never logged, never returned
    nvidia_api_key: SecretStr = SecretStr("")
    anthropic_api_key: SecretStr = SecretStr("")
    ai_base_url: str = ""
    ai_model: str = ""
    # Tried in turn when the main model is overloaded (503), rate limited (429) or slow.
    ai_fallback_models: str = ""  # comma-separated; empty = provider default
    ai_effort: Literal["low", "medium", "high", "xhigh", "max"] = "high"  # Claude only
    ai_timeout_s: int = 0  # per attempt; 0 = provider default
    ai_max_jobs_per_hour: int = 5

    @property
    def ai_api_key(self) -> SecretStr:
        """The key of the selected provider."""
        return {
            "gemini": self.gemini_api_key,
            "nvidia": self.nvidia_api_key,
            "anthropic": self.anthropic_api_key,
        }[self.ai_provider]

    @property
    def ai_endpoint(self) -> str:
        return self.ai_base_url or AI_PROVIDER_DEFAULTS[self.ai_provider]["base_url"]

    @property
    def ai_models(self) -> list[str]:
        """The main model first, then the fallbacks, without repeats."""
        defaults = AI_PROVIDER_DEFAULTS[self.ai_provider]
        main = self.ai_model or defaults["model"]
        fallbacks = [m.strip() for m in self.ai_fallback_models.split(",") if m.strip()]
        if not self.ai_fallback_models and not self.ai_model:
            fallbacks = list(defaults["fallbacks"])
        return list(dict.fromkeys([main, *fallbacks]))

    @property
    def ai_attempt_timeout_s(self) -> int:
        return self.ai_timeout_s or AI_PROVIDER_DEFAULTS[self.ai_provider]["timeout_s"]

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
