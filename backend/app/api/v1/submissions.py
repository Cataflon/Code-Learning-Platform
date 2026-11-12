from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import (
    CurrentUser,
    DbSession,
    MemberAssignment,
    StudentUser,
    ViewableSubmission,
)
from app.runner.base import Runner
from app.runner.factory import get_runner
from app.schemas.submission import SubmissionCreate, SubmissionRead, SubmissionSummary
from app.services import submission_service

router = APIRouter(tags=["submissions"])


@router.post(
    "/assignments/{assignment_id}/submissions",
    response_model=SubmissionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_submission(
    data: SubmissionCreate,
    assignment: MemberAssignment,
    db: DbSession,
    user: StudentUser,
    runner: Annotated[Runner, Depends(get_runner)],
):
    """Synchronous in this step: the response arrives after every test has run."""
    submission = submission_service.create_submission(db, user, assignment, data.code)
    submission_service.evaluate_submission(db, submission, runner)
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
