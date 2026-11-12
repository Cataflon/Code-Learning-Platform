"""Application factory."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import assignments, auth, concepts, courses, health, test_cases, users
from app.core.config import get_settings
from app.core.errors import register_error_handlers


def build_api_router() -> APIRouter:
    api = APIRouter(prefix="/api/v1")
    api.include_router(auth.router)
    api.include_router(users.router)
    api.include_router(courses.router)
    api.include_router(concepts.router)
    api.include_router(assignments.router)
    api.include_router(test_cases.router)
    return api


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Autograder API", version="0.1.0")
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
