"""Background evaluation of a submission, and recovery after a server restart."""

import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Submission, SubmissionStatus
from app.runner.base import Runner
from app.services import submission_service

logger = logging.getLogger(__name__)

INTERRUPTED_MESSAGE = (
    "The server restarted while this submission was being evaluated. Submit again."
)


def run_submission(
    submission_id: int,
    session_factory: Callable[[], Session],
    runner: Runner,
    slots: threading.BoundedSemaphore,
) -> None:
    """Evaluate one submission. Runs after the HTTP response has been sent.

    It takes only an id and opens **its own** database session: the request's session is
    closed as soon as the response leaves, so it must not be used here. Because the function
    needs nothing but the id, it could later move to a separate worker unchanged.
    """
    with slots:  # waits here while the maximum number of evaluations is already running
        db = session_factory()
        try:
            submission = db.get(Submission, submission_id)
            if submission is None or submission.status != SubmissionStatus.queued:
                return  # deleted meanwhile, or already picked up
            submission_service.evaluate_submission(db, submission, runner)
        except Exception:
            logger.exception("Background evaluation of submission %s crashed", submission_id)
            db.rollback()
            _mark_error(db, submission_id, "The submission could not be evaluated.")
        finally:
            db.close()


def _mark_error(db: Session, submission_id: int, message: str) -> None:
    submission = db.get(Submission, submission_id)
    if submission is not None and submission.status != SubmissionStatus.done:
        submission.status = SubmissionStatus.error
        submission.error_message = message
        submission.finished_at = datetime.now(UTC)
        db.commit()


def recover_interrupted_submissions(db: Session) -> int:
    """At startup: whatever was still queued or running was lost with the old process."""
    stuck = list(
        db.scalars(
            select(Submission).where(
                Submission.status.in_([SubmissionStatus.queued, SubmissionStatus.running])
            )
        )
    )
    for submission in stuck:
        submission.status = SubmissionStatus.error
        submission.error_message = INTERRUPTED_MESSAGE
        submission.finished_at = datetime.now(UTC)
    db.commit()
    if stuck:
        logger.warning("Marked %d interrupted submission(s) as error", len(stuck))
    return len(stuck)
