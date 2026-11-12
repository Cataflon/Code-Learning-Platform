"""Single place that decides which Runner the application uses, and how many run at once."""

import threading
from functools import lru_cache

from app.core.config import Settings, get_settings
from app.runner.base import Runner


def build_runner(settings: Settings) -> Runner:
    if settings.runner == "subprocess":
        # Settings validation already refuses this outside ENV=dev; check again, defensively.
        if settings.env != "dev":
            raise RuntimeError("SubprocessRunner is only allowed when ENV=dev")
        from app.runner.subprocess_runner import SubprocessRunner

        return SubprocessRunner()
    from app.runner.docker_runner import DockerRunner

    return DockerRunner(
        image=settings.sandbox_image,
        cpus=settings.sandbox_cpus,
        pids_limit=settings.sandbox_pids_limit,
        startup_margin_ms=settings.sandbox_startup_margin_ms,
    )


@lru_cache
def get_runner() -> Runner:
    """FastAPI dependency; tests override it with a FakeRunner."""
    return build_runner(get_settings())


@lru_cache
def get_run_slots() -> threading.BoundedSemaphore:
    """Global semaphore: at most ``max_concurrent_runs`` submissions are evaluated at once.

    A submission runs its tests one after another, so this is also the maximum number of
    sandbox containers alive at the same time.
    """
    return threading.BoundedSemaphore(get_settings().max_concurrent_runs)
