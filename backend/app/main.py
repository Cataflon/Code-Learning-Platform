"""Application factory."""

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
from app.services.submission_runner import recover_interrupted_submissions


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
    yield


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
