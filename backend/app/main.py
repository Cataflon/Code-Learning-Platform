"""Application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    assignments,
    auth,
    concepts,
    courses,
    health,
    submissions,
    test_cases,
    users,
)
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.db.session import get_background_session_factory
from app.runner.factory import get_runner
from app.services.submission_runner import recover_interrupted_submissions

logger = logging.getLogger(__name__)


def build_api_router() -> APIRouter:
    api = APIRouter(prefix="/api/v1")
    api.include_router(auth.router)
    api.include_router(users.router)
    api.include_router(courses.router)
    api.include_router(concepts.router)
    api.include_router(assignments.router)
    api.include_router(test_cases.router)
    api.include_router(submissions.router)
    return api


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup hook: submissions left queued or running by a previous process become errors."""
    # Going through dependency_overrides keeps tests away from the development database.
    provider = app.dependency_overrides.get(
        get_background_session_factory, get_background_session_factory
    )
    db = provider()()
    try:
        recover_interrupted_submissions(db)
    finally:
        db.close()
    remove_orphaned_sandboxes(app)
    yield


def remove_orphaned_sandboxes(app: FastAPI) -> None:
    """A killed server cannot run its cleanup code, so stale containers are removed here."""
    runner = app.dependency_overrides.get(get_runner, get_runner)()
    cleanup = getattr(runner, "remove_leftover_containers", None)
    if cleanup is None:
        return
    try:
        removed = cleanup()
    except Exception as exc:  # Docker not running: the API still starts, submissions will fail
        logger.warning("Could not check for leftover sandbox containers: %s", exc)
        return
    if removed:
        logger.warning("Removed %d leftover sandbox container(s)", removed)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Autograder API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    # /health lives outside /api/v1 on purpose (see the API contract).
    app.include_router(health.router)
    app.include_router(build_api_router())
    return app


app = create_app()
