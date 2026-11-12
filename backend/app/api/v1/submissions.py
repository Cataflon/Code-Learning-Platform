from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session, sessionmaker

from app.core.deps import (
    CurrentUser,
    DbSession,
    MemberAssignment,
    StudentUser,
    ViewableSubmission,
)
from app.db.session import get_background_session_factory
from app.runner.base import Runner
from app.runner.factory import get_run_slots, get_runner
from app.schemas.dashboard import SubmissionPage
from app.schemas.submission import SubmissionCreate, SubmissionRead
from app.services import dashboard_service, submission_service
from app.services.dashboard_service import VerdictFilter
from app.services.submission_runner import run_submission

router = APIRouter(tags=["submissions"])


@router.post(
    "/assignments/{assignment_id}/submissions",
    response_model=SubmissionRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_submission(
    data: SubmissionCreate,
    assignment: MemberAssignment,
    db: DbSession,
    user: StudentUser,
    background: BackgroundTasks,
    runner: Annotated[Runner, Depends(get_runner)],
    session_factory: Annotated[sessionmaker[Session], Depends(get_background_session_factory)],
):
    """Answers 202 at once with status ``queued``; the tests run after the response is sent.

    The client then polls GET /submissions/{id} until the status is ``done`` or ``error``.
    """
    submission = submission_service.create_submission(db, user, assignment, data.code)
    background.add_task(run_submission, submission.id, session_factory, runner, get_run_slots())
    return submission_service.to_read(db, submission, user)


@router.get("/assignments/{assignment_id}/submissions", response_model=SubmissionPage)
def list_submissions(
    assignment: MemberAssignment,
    db: DbSession,
    user: CurrentUser,
    verdict: VerdictFilter = "all",
    q: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Student: their own attempts. Teacher: the class, filtered, searched and paginated."""
    return dashboard_service.search_submissions(db, assignment, user, verdict, q, page, page_size)


@router.get("/submissions/{submission_id}", response_model=SubmissionRead)
def get_submission(submission: ViewableSubmission, db: DbSession, user: CurrentUser):
    return submission_service.to_read(db, submission, user)
