"""A simple rate limit (Step 10): a fixed-window counter per key, kept in memory.

``FixedWindowLimiter(limit, window_s)`` lets at most ``limit`` hits per key in each window of
``window_s`` seconds; the next one gets 429 with ``Retry-After``. A fixed window is the simplest
kind: its known weakness is a burst at the edge of two windows (up to twice the limit in a short
time), acceptable here. The state lives in the process, which fits the single-process server of
this project; several processes would need a shared store such as Redis.

Used as FastAPI dependencies on sign-in and registration (per IP address), on submissions and on
material uploads (per user).
"""

import threading
import time
from collections.abc import Callable
from math import ceil

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import TooManyRequestsError


class FixedWindowLimiter:
    def __init__(self, limit: int, window_s: float, clock: Callable[[], float] = time.monotonic):
        self.limit = limit
        self.window_s = window_s
        self.clock = clock
        self._hits: dict[str, tuple[float, int]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str) -> float | None:
        """Count one hit; return None when allowed, or the seconds to wait when over the limit."""
        now = self.clock()
        with self._lock:
            start, count = self._hits.get(key, (now, 0))
            if now - start >= self.window_s:
                start, count = now, 0
            if count >= self.limit:
                return start + self.window_s - now
            self._hits[key] = (start, count + 1)
            if len(self._hits) > 10_000:  # forget old windows so memory stays small
                self._hits = {k: v for k, v in self._hits.items() if now - v[0] < self.window_s}
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


_limiters: dict[str, FixedWindowLimiter] = {}


def limiter(name: str, limit: int, window_s: float) -> FixedWindowLimiter:
    """One limiter per name, created on first use with the current settings."""
    existing = _limiters.get(name)
    if existing is None or (existing.limit, existing.window_s) != (limit, window_s):
        existing = _limiters[name] = FixedWindowLimiter(limit, window_s)
    return existing


def reset_all() -> None:
    """Tests start every case with empty counters."""
    for item in _limiters.values():
        item.reset()


def _check(name: str, key: str, limit: int, window_s: float, what: str) -> None:
    if not get_settings().rate_limit_enabled:
        return
    wait = limiter(name, limit, window_s).hit(key)
    if wait is not None:
        seconds = max(1, ceil(wait))
        raise TooManyRequestsError(
            f"Too many {what}; try again in {seconds} s", headers={"Retry-After": str(seconds)}
        )


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def limit_sign_in(request: Request) -> None:
    """Sign-in and registration: per IP address, against password guessing and account spam."""
    settings = get_settings()
    _check(
        f"auth:{request.url.path}",
        client_ip(request),
        settings.rate_limit_login_per_minute,
        60,
        "attempts",
    )


def limit_per_user(name: str, limit_of: Callable, window_s: float, what: str) -> Callable:
    """A dependency counting hits per signed-in user (the user id comes from the token)."""
    from app.core.deps import CurrentUser  # here, to avoid an import cycle

    def dependency(user: CurrentUser) -> None:
        _check(name, str(user.id), limit_of(get_settings()), window_s, what)

    return dependency


limit_submissions = limit_per_user(
    "submissions", lambda s: s.rate_limit_submissions_per_minute, 60, "submissions"
)
limit_uploads = limit_per_user(
    "uploads", lambda s: s.rate_limit_uploads_per_10_minutes, 600, "uploads"
)
