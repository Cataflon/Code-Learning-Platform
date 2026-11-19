"""Logging with a request id (Step 10).

Every request gets an id: the one the client sent in ``X-Request-ID`` (when it looks safe) or a
new random one. It goes into a context variable, so every log line written while the request
is handled carries it, including the lines of background tasks started by that request, and it
is sent back in the ``X-Request-ID`` response header. When something fails, searching the log for
that id shows the whole path of the request.
"""

import logging
import re
import time
import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

HEADER = "X-Request-ID"
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_configured = False

access_logger = logging.getLogger("app.access")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    """One format for the whole app: time, level, request id, logger, message."""
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s")
    )
    root = logging.getLogger("app")
    root.setLevel(level.upper())
    root.addHandler(handler)
    root.propagate = False
    _configured = True


def new_request_id(incoming: str | None) -> str:
    """Keep the caller's id when it is a short, plain token; otherwise make a new one."""
    if incoming and _SAFE_ID.match(incoming):
        return incoming
    return uuid.uuid4().hex


class RequestIdMiddleware:
    """Pure ASGI middleware: sets the request id, adds the header, logs one access line."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        incoming = headers.get(HEADER.lower().encode(), b"").decode("latin-1")
        request_id = new_request_id(incoming)
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status = 500

        async def send_with_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message.setdefault("headers", [])
                message["headers"].append((HEADER.encode(), request_id.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            access_logger.info(
                "%s %s -> %s in %.0f ms", scope["method"], scope["path"], status, elapsed
            )
            request_id_var.reset(token)
