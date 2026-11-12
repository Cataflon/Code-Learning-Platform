"""Submissions: creation rules, evaluation loop and what each viewer is allowed to see."""

import logging
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ConflictError, InvalidDataError, NotFoundError
from app.models import Assignment, Role, Submission, SubmissionStatus, TestCase, TestResult, User
from app.models.submission import Verdict
from app.runner.base import Limits, Runner
from app.schemas.submission import SubmissionRead, SubmissionSummary, TestResultRead
from app.services.scoring import compute_score, count_passed, decide_verdict, extract_error_excerpt

logger = logging.getLogger(__name__)

MAX_STORED_OUTPUT = 4000  # characters of stdout / stderr kept per test


def count_submissions(db: Session, student_id: int, assignment_id: int) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Submission)
        .where(Submission.student_id == student_id, Submission.assignment_id == assignment_id)
    )


def submissions_left(db: Session, student: User, assignment: Assignment) -> int:
    return max(0, assignment.max_submissions - count_submissions(db, student.id, assignment.id))


def create_submission(db: Session, student: User, assignment: Assignment, code: str) -> Submission:
    if not assignment.test_cases:
        raise InvalidDataError("This assignment has no tests yet")
    if assignment.status == "closed":
        raise ConflictError("The deadline for this assignment has passed")
    if submissions_left(db, student, assignment) <= 0:
        raise ConflictError("You have no attempts left for this assignment")
    submission = Submission(
        assignment_id=assignment.id,
        student_id=student.id,
        code=code,
        language=assignment.language,
        status=SubmissionStatus.queued,
        total_count=len(assignment.test_cases),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def evaluate_submission(db: Session, submission: Submission, runner: Runner) -> Submission:
    """Run every test in order, saving each result as soon as it is known.

    Committing after every test is what lets the page show progress while polling.
    Any unexpected failure ends in status ``error``; a submission is never left ``running``.
    """
    assignment = submission.assignment
    test_cases = list(assignment.test_cases)
    limits = Limits(
        time_limit_ms=assignment.time_limit_ms, memory_limit_mb=assignment.memory_limit_mb
    )
    submission.status = SubmissionStatus.running
    submission.started_at = datetime.now(UTC)
    submission.total_count = len(test_cases)
    db.commit()

    verdicts: dict[int, Verdict] = {}
    try:
        for test_case in test_cases:
            run = runner.run(submission.code, test_case.input_data, limits)
            verdict = decide_verdict(run, test_case.expected_output)
            verdicts[test_case.id] = verdict
            db.add(
                TestResult(
                    submission_id=submission.id,
                    test_case_id=test_case.id,
                    verdict=verdict,
                    actual_output=run.stdout[:MAX_STORED_OUTPUT],
                    stderr=run.stderr[:MAX_STORED_OUTPUT],
                    runtime_ms=run.runtime_ms,
                )
            )
            if verdict == Verdict.runtime_error and submission.error_excerpt is None:
                submission.error_excerpt = extract_error_excerpt(run.stderr)
            submission.passed_count = count_passed(verdicts.values())
            db.commit()
    except Exception as exc:  # the runner itself failed (Docker down, disk full, ...)
        logger.exception("Evaluation of submission %s failed", submission.id)
        db.rollback()
        submission.status = SubmissionStatus.error
        submission.error_message = f"The submission could not be evaluated: {exc}"[:500]
        submission.finished_at = datetime.now(UTC)
        db.commit()
        return submission

    weights = {test_case.id: test_case.weight for test_case in test_cases}
    submission.score = compute_score(verdicts, weights)
    submission.passed_count = count_passed(verdicts.values())
    submission.status = SubmissionStatus.done
    submission.finished_at = datetime.now(UTC)
    db.commit()
    db.refresh(submission)
    return submission


def get_submission(db: Session, submission_id: int) -> Submission:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise NotFoundError("Submission not found")
    return submission


def list_submissions(
    db: Session, assignment: Assignment, viewer: User, limit: int = 100, offset: int = 0
) -> list[Submission]:
    """Student: only their own attempts. Teacher: everyone's. Newest first."""
    query = (
        select(Submission)
        .where(Submission.assignment_id == assignment.id)
        .options(selectinload(Submission.results), selectinload(Submission.student))
    )
    if viewer.role == Role.student:
        query = query.where(Submission.student_id == viewer.id)
    query = query.order_by(Submission.created_at.desc(), Submission.id.desc())
    return list(db.scalars(query.limit(limit).offset(offset)))


def attempt_numbers(db: Session, submissions: list[Submission]) -> dict[int, int]:
    """Submission id -> 1-based attempt number of that student on that assignment."""
    if not submissions:
        return {}
    numbered = (
        select(
            Submission.id,
            func.row_number()
            .over(
                partition_by=(Submission.student_id, Submission.assignment_id),
                order_by=(Submission.created_at, Submission.id),
            )
            .label("attempt"),
        )
        .where(Submission.assignment_id.in_({s.assignment_id for s in submissions}))
        .where(Submission.student_id.in_({s.student_id for s in submissions}))
        .subquery()
    )
    wanted = [s.id for s in submissions]
    rows = db.execute(select(numbered.c.id, numbered.c.attempt).where(numbered.c.id.in_(wanted)))
    return dict(rows.all())


# --- views -----------------------------------------------------------------------------------


def hidden_labels(test_cases: list[TestCase]) -> dict[int, str]:
    """Students never learn a hidden test's name: it is shown as ``Hidden test #n``."""
    labels: dict[int, str] = {}
    for test_case in test_cases:
        if test_case.is_hidden:
            labels[test_case.id] = f"Hidden test #{len(labels) + 1}"
    return labels


def _visible_tests(submission: Submission) -> list[TestCase]:
    """While running: every test (pending ones included). Afterwards: only the tests that ran."""
    test_cases = list(submission.assignment.test_cases)
    if submission.status in (SubmissionStatus.queued, SubmissionStatus.running):
        return test_cases
    ran = {result.test_case_id for result in submission.results}
    return [test_case for test_case in test_cases if test_case.id in ran]


def get_visible_results(submission: Submission, viewer: User) -> list[TestResultRead]:
    by_test = {result.test_case_id: result for result in submission.results}
    test_cases = _visible_tests(submission)
    labels = hidden_labels(list(submission.assignment.test_cases))
    is_teacher = viewer.role == Role.teacher
    items = []
    for test_case in test_cases:
        result = by_test.get(test_case.id)
        failed = result is not None and result.verdict != Verdict.passed
        masked = test_case.is_hidden and not is_teacher
        items.append(
            TestResultRead(
                test_case_id=test_case.id,
                name=labels[test_case.id] if masked else test_case.name,
                position=test_case.position,
                is_hidden=test_case.is_hidden,
                verdict=result.verdict if result else None,
                runtime_ms=result.runtime_ms if result else None,
                concepts=[concept.name for concept in test_case.concepts],
                # The hint is shown only for a failed test, even when the test is hidden.
                hint=test_case.hint if (failed or is_teacher) else None,
                input_data=None if masked else test_case.input_data,
                expected_output=None if masked else test_case.expected_output,
                actual_output=None if masked or result is None else result.actual_output,
                stderr=None if masked or result is None else result.stderr,
            )
        )
    return items


def to_summary(submission: Submission, attempt_number: int) -> SubmissionSummary:
    by_test = {result.test_case_id: result.verdict for result in submission.results}
    return SubmissionSummary(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        student_name=submission.student.full_name,
        attempt_number=attempt_number,
        status=submission.status,
        score=submission.score,
        passed_count=submission.passed_count,
        total_count=submission.total_count,
        verdicts=[by_test.get(test_case.id) for test_case in _visible_tests(submission)],
        error_excerpt=submission.error_excerpt,
        created_at=submission.created_at,
        started_at=submission.started_at,
        finished_at=submission.finished_at,
    )


def to_read(db: Session, submission: Submission, viewer: User) -> SubmissionRead:
    attempt = attempt_numbers(db, [submission]).get(submission.id, 1)
    summary = to_summary(submission, attempt)
    return SubmissionRead(
        **summary.model_dump(),
        code=submission.code,
        error_message=submission.error_message,
        results=get_visible_results(submission, viewer),
    )


def to_summaries(db: Session, submissions: list[Submission]) -> list[SubmissionSummary]:
    numbers = attempt_numbers(db, submissions)
    return [to_summary(submission, numbers.get(submission.id, 1)) for submission in submissions]
