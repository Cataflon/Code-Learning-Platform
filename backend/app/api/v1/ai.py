from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, sessionmaker

from app.ai.client import LLMClient, get_llm_client
from app.core.config import get_settings
from app.core.deps import DbSession, OwnedAssignment, OwnedTestCase, TeacherUser
from app.core.errors import NotFoundError
from app.db.session import get_background_session_factory
from app.runner.base import Runner
from app.runner.factory import get_run_slots, get_runner
from app.schemas.assignment import TestCaseRead
from app.services import ai_service

router = APIRouter(tags=["ai"])


class ConfigRead(BaseModel):
    ai_available: bool


class GenerateTestsRequest(BaseModel):
    reference_solution: str = Field(min_length=1, max_length=64 * 1024)  # the teacher's
    count: int = Field(default=8, ge=4, le=12)


class JobCreated(BaseModel):
    job_id: int


class GenerationJobRead(BaseModel):
    id: int
    assignment_id: int
    status: str
    phase: str  # queued | writing | sandbox | linking | done | error
    model: str
    tests_requested: int
    tests_proposed: int | None
    tests_kept: int | None
    input_tokens: int
    output_tokens: int
    error_message: str | None
    reference_code: str | None  # the teacher's solution, only sent back to them
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class ApprovedCount(BaseModel):
    approved: int


def require_ai() -> None:
    ai_service.ensure_available()


@router.get("/config", response_model=ConfigRead)
def config():
    """What the frontend needs to know about this server (whether to show the AI button)."""
    return ConfigRead(ai_available=get_settings().ai_available)


@router.post(
    "/assignments/{assignment_id}/generate-tests",
    response_model=JobCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_tests(
    assignment: OwnedAssignment,
    _available: Annotated[None, Depends(require_ai)],
    user: TeacherUser,
    db: DbSession,
    background: BackgroundTasks,
    llm: Annotated[LLMClient, Depends(get_llm_client)],
    runner: Annotated[Runner, Depends(get_runner)],
    session_factory: Annotated[sessionmaker[Session], Depends(get_background_session_factory)],
    data: GenerateTestsRequest,
):
    """Starts a job and answers 202 at once; poll GET /generation-jobs/{id} for progress.

    The teacher sends the reference solution; the model only proposes the test inputs.
    """
    job = ai_service.start_generation(db, assignment, user, data.count, data.reference_solution)
    background.add_task(
        ai_service.run_generation, job.id, session_factory, llm, runner, get_run_slots()
    )
    return JobCreated(job_id=job.id)


@router.get("/generation-jobs/{job_id}", response_model=GenerationJobRead)
def get_generation_job(job_id: int, db: DbSession, user: TeacherUser):
    job = ai_service.get_job(db, job_id)
    if job.assignment.course.teacher_id != user.id:
        raise NotFoundError("Generation job not found")
    return GenerationJobRead(
        id=job.id,
        assignment_id=job.assignment_id,
        status=job.status.value,
        phase=ai_service.phase_of(job),
        model=job.model,
        tests_requested=job.tests_requested,
        tests_proposed=job.tests_proposed,
        tests_kept=job.tests_kept,
        input_tokens=job.input_tokens,
        output_tokens=job.output_tokens,
        error_message=job.error_message,
        reference_code=job.reference_code,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.post("/test-cases/{test_case_id}/approve", response_model=TestCaseRead)
def approve_test_case(test_case: OwnedTestCase, db: DbSession):
    return ai_service.approve(db, test_case)


@router.post("/assignments/{assignment_id}/tests/approve-all", response_model=ApprovedCount)
def approve_all_tests(assignment: OwnedAssignment, db: DbSession):
    return ApprovedCount(approved=ai_service.approve_all(db, assignment))
