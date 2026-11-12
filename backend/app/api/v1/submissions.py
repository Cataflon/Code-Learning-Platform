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
from app.schemas.submission import SubmissionCreate, SubmissionRead, SubmissionSummary
from app.services import submission_service
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


@router.get("/assignments/{assignment_id}/submissions", response_model=list[SubmissionSummary])
def list_submissions(
    assignment: MemberAssignment,
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    submissions = submission_service.list_submissions(db, assignment, user, limit, offset)
    return submission_service.to_summaries(db, submissions)


@router.get("/submissions/{submission_id}", response_model=SubmissionRead)
def get_submission(submission: ViewableSubmission, db: DbSession, user: CurrentUser):
    return submission_service.to_read(db, submission, user)
