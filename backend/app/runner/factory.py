"""Single place that decides which Runner the application uses."""

from functools import lru_cache

from app.runner.base import Runner
from app.runner.subprocess_runner import SubprocessRunner


@lru_cache
def get_runner() -> Runner:
    """FastAPI dependency; tests override it with a FakeRunner."""
    return SubprocessRunner()
