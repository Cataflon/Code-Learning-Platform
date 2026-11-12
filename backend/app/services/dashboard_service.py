"""Read-only aggregates: student dashboard, teacher statistics, submissions list, activity.

The page asks one endpoint and the database does the counting. Without these endpoints the
frontend would need dozens of small requests per page (the N+1 problem, moved to the network).
"""

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Assignment,
    Course,
    Enrollment,
    Role,
    Submission,
    SubmissionStatus,
    TestResult,
    User,
    Verdict,
)
from app.schemas.assignment import ResultBuckets
from app.schemas.dashboard import (
    Activity,
    ActivityDay,
    ActivityTotals,
    AssignmentStats,
    CourseStats,
    DashboardAssignment,
    DashboardCourse,
    DashboardStats,
    DashboardSubmission,
    ScoreBucket,
    StudentDashboard,
    SubmissionCounts,
    SubmissionPage,
    TestStat,
)
from app.services import submission_service

IN_PROGRESS = (SubmissionStatus.queued, SubmissionStatus.running)
SCORE_BUCKETS = [("0–25%", 0, 25), ("26–50%", 26, 50), ("51–75%", 51, 75), ("76–99%", 76, 99)]
VerdictFilter = Literal["all", "correct", "partial", "wrong", "running"]


def _enrolled(query: Select, course_id_column) -> Select:
    """Keep only submissions of students still enrolled: who left is out of the reports."""
    return query.join(
        Enrollment,
        and_(
            Enrollment.user_id == Submission.student_id,
            Enrollment.course_id == course_id_column,
        ),
    )


# --- student dashboard -----------------------------------------------------------------------


def student_dashboard(db: Session, student: User) -> StudentDashboard:
    courses = list(
        db.scalars(
            select(Course)
            .join(Enrollment, Enrollment.course_id == Course.id)
            .where(Enrollment.user_id == student.id)
            .order_by(Course.title)
        )
    )
    course_by_id = {course.id: course for course in courses}
    assignments = list(
        db.scalars(
            select(Assignment)
            .where(Assignment.course_id.in_(course_by_id), Assignment.is_published.is_(True))
            .options(selectinload(Assignment.test_cases))
            .order_by(Assignment.due_at.nulls_last(), Assignment.id)
        )
    )
    # Every attempt of this student on those assignments, newest first (at most
    # max_submissions per assignment, so loading them is cheap).
    submissions = list(
        db.scalars(
            select(Submission)
            .where(
                Submission.student_id == student.id,
                Submission.assignment_id.in_([assignment.id for assignment in assignments]),
            )
            .options(selectinload(Submission.results))
            .order_by(Submission.created_at.desc(), Submission.id.desc())
        )
    )
    by_assignment: dict[int, list[Submission]] = {}
    for submission in submissions:
        by_assignment.setdefault(submission.assignment_id, []).append(submission)

    items = []
    for assignment in assignments:
        attempts = by_assignment.get(assignment.id, [])
        scores = [attempt.score for attempt in attempts if attempt.score is not None]
        latest = attempts[0] if attempts else None
        course = course_by_id[assignment.course_id]
        items.append(
            DashboardAssignment(
                id=assignment.id,
                title=assignment.title,
                course_id=course.id,
                course_title=course.title,
                course_color=course.color,
                due_at=assignment.due_at,
                status=assignment.status,
                test_count=assignment.test_count,
                max_submissions=assignment.max_submissions,
                attempts_used=len(attempts),
                best_score=max(scores) if scores else None,
                last_verdicts=_verdicts(latest) if latest else [],
                last_submission_status=latest.status if latest else None,
            )
        )

    title_by_id = {assignment.id: assignment.title for assignment in assignments}
    recent = [
        DashboardSubmission(
            id=submission.id,
            assignment_id=submission.assignment_id,
            assignment_title=title_by_id[submission.assignment_id],
            status=submission.status,
            score=submission.score,
            verdicts=_verdicts(submission),
            created_at=submission.created_at,
        )
        for submission in submissions[:5]
    ]
    best_scores = [item.best_score for item in items if item.best_score is not None]
    stats = DashboardStats(
        to_submit=sum(1 for item in items if item.status == "open" and item.best_score != 100),
        average_best_score=round(sum(best_scores) / len(best_scores)) if best_scores else None,
        concepts_to_review=0,
    )
    return StudentDashboard(
        stats=stats,
        courses=[
            DashboardCourse(
                id=course.id,
                title=course.title,
                color=course.color,
                teacher_name=course.teacher_name,
            )
            for course in courses
        ],
        assignments=items,
        recent_submissions=recent,
        concepts_to_review=[],  # filled in by the concept report (Step 7)
    )


def _verdicts(submission: Submission) -> list[Verdict | None]:
    """Verdict squares of one submission, in test order."""
    return submission_service.to_summary(submission, 0).verdicts


# --- teacher: one assignment -----------------------------------------------------------------


def _best_submission_ids(assignment_id: int) -> Select:
    """Each enrolled student's best finished submission (highest score, then the newest).

    ``DISTINCT ON (student_id)`` keeps the first row of every student in the given order,
    which is PostgreSQL's direct way of saying "one row per group".
    """
    query = (
        select(Submission.id, Submission.score)
        .where(
            Submission.assignment_id == assignment_id,
            Submission.status == SubmissionStatus.done,
        )
        .ext(distinct_on(Submission.student_id))
        .order_by(Submission.student_id, Submission.score.desc(), Submission.created_at.desc())
    )
    return _enrolled(
        query.join(Assignment, Assignment.id == Submission.assignment_id), Assignment.course_id
    )


def assignment_stats(db: Session, assignment: Assignment) -> AssignmentStats:
    enrolled_count = db.scalar(
        select(func.count())
        .select_from(Enrollment)
        .where(Enrollment.course_id == assignment.course_id)
    )
    # COUNT(*) FILTER (WHERE ...) counts only the rows that meet a condition, in the same pass.
    totals = db.execute(
        _enrolled(
            select(
                func.count().label("submissions"),
                func.count(Submission.student_id.distinct()).label("students"),
                func.count().filter(Submission.status.in_(IN_PROGRESS)).label("running"),
            ).where(Submission.assignment_id == assignment.id),
            assignment.course_id,
        )
    ).one()

    best = _best_submission_ids(assignment.id).subquery()
    scores = list(db.scalars(select(best.c.score)))
    per_test = {
        row.test_case_id: row
        for row in db.execute(
            select(
                TestResult.test_case_id,
                func.count().label("total"),
                func.count().filter(TestResult.verdict == Verdict.passed).label("passed"),
            )
            .where(TestResult.submission_id.in_(select(best.c.id)))
            .group_by(TestResult.test_case_id)
        )
    }
    tests = []
    for test_case in assignment.test_cases:
        row = per_test.get(test_case.id)
        total, passed = (row.total, row.passed) if row else (0, 0)
        tests.append(
            TestStat(
                test_case_id=test_case.id,
                name=test_case.name,
                is_hidden=test_case.is_hidden,
                concepts=[concept.name for concept in test_case.concepts],
                passed=passed,
                total=total,
                pass_rate=passed / total if total else None,
            )
        )
    return AssignmentStats(
        submission_count=totals.submissions,
        submitted_count=totals.students,
        enrolled_count=enrolled_count,
        running_count=totals.running,
        average_score=round(sum(scores) / len(scores)) if scores else None,
        tests=tests,
        score_distribution=score_distribution(scores),
    )


def score_distribution(scores: list[int]) -> list[ScoreBucket]:
    """Pure: how many scores fall in each band. 100% has a band of its own."""
    buckets = [
        ScoreBucket(label=label, count=sum(1 for score in scores if low <= score <= high))
        for label, low, high in SCORE_BUCKETS
    ]
    buckets.append(ScoreBucket(label="100%", count=sum(1 for score in scores if score == 100)))
    return buckets


# --- teacher: the whole course ---------------------------------------------------------------


def _best_per_student(course_id: int):
    """Subquery: best score of each enrolled student on each assignment of the course."""
    query = (
        select(
            Submission.assignment_id,
            Submission.student_id,
            func.max(func.coalesce(Submission.score, 0)).label("best"),
        )
        .join(Assignment, Assignment.id == Submission.assignment_id)
        .where(Assignment.course_id == course_id)
        .group_by(Submission.assignment_id, Submission.student_id)
    )
    return _enrolled(query, Assignment.course_id).subquery()


def assignment_overview(db: Session, course: Course) -> dict[int, tuple[int, ResultBuckets]]:
    """Assignment id -> (students who submitted, their best results in three buckets)."""
    best = _best_per_student(course.id)
    rows = db.execute(
        select(
            best.c.assignment_id,
            func.count().label("submitted"),
            func.count().filter(best.c.best == 100).label("full"),
            func.count().filter(and_(best.c.best > 0, best.c.best < 100)).label("partial"),
            func.count().filter(best.c.best == 0).label("none"),
        ).group_by(best.c.assignment_id)
    )
    return {
        row.assignment_id: (
            row.submitted,
            ResultBuckets(full=row.full, partial=row.partial, none=row.none),
        )
        for row in rows
    }


def course_stats(db: Session, course: Course) -> CourseStats:
    students = db.scalar(
        select(func.count()).select_from(Enrollment).where(Enrollment.course_id == course.id)
    )
    midnight = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    submissions_today = db.scalar(
        _enrolled(
            select(func.count())
            .select_from(Submission)
            .join(Assignment, Assignment.id == Submission.assignment_id)
            .where(Assignment.course_id == course.id, Submission.created_at >= midnight),
            Assignment.course_id,
        )
    )
    best = _best_per_student(course.id)
    average = db.scalar(select(func.avg(best.c.best)))
    return CourseStats(
        students=students,
        submissions_today=submissions_today,
        average_score=round(average) if average is not None else None,
    )


# --- submissions list ------------------------------------------------------------------------


def _categories(status, score) -> dict:
    """The filter tabs, as SQL conditions over a status column and a score column."""
    done = status == SubmissionStatus.done
    return {
        "correct": and_(done, score == 100),
        "partial": and_(done, score > 0, score < 100),
        "wrong": or_(and_(done, score == 0), status == SubmissionStatus.error),
        "running": status.in_(IN_PROGRESS),
    }


def search_submissions(
    db: Session,
    assignment: Assignment,
    viewer: User,
    verdict: VerdictFilter = "all",
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> SubmissionPage:
    """Student: their own attempts. Teacher: the class, with filter, search and pagination."""
    conditions = [Submission.assignment_id == assignment.id]
    if viewer.role == Role.student:
        conditions.append(Submission.student_id == viewer.id)
    base = select(Submission).join(User, User.id == Submission.student_id).where(*conditions)
    if viewer.role == Role.teacher:
        base = _enrolled(base, assignment.course_id)
        if q and q.strip():
            base = base.where(User.full_name.ilike(f"%{_escape_like(q.strip())}%", escape="\\"))

    scope = base.subquery()
    # One pass over the matching rows gives the number shown on every filter tab.
    counted = select(
        func.count().label("all"),
        *[
            func.count().filter(condition).label(name)
            for name, condition in _categories(scope.c.status, scope.c.score).items()
        ],
    ).select_from(scope)
    counts = SubmissionCounts(**db.execute(counted).one()._asdict())

    filtered = base
    if verdict != "all":
        filtered = base.where(_categories(Submission.status, Submission.score)[verdict])
    submissions = list(
        db.scalars(
            filtered.options(selectinload(Submission.results), selectinload(Submission.student))
            .order_by(Submission.created_at.desc(), Submission.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    )
    return SubmissionPage(
        items=submission_service.to_summaries(db, submissions),
        total=getattr(counts, verdict),
        page=page,
        page_size=page_size,
        counts=counts,
    )


def _escape_like(text: str) -> str:
    """% and _ typed by the user must match themselves, not act as wildcards."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# --- profile activity ------------------------------------------------------------------------


def user_activity(db: Session, user: User, weeks: int = 14, today: date | None = None) -> Activity:
    today = today or datetime.now(UTC).date()
    start = today - timedelta(days=weeks * 7 - 1)
    day = func.date(func.timezone("UTC", Submission.created_at))
    # One GROUP BY: submissions per calendar day.
    rows = db.execute(
        select(day.label("day"), func.count().label("count"))
        .where(Submission.student_id == user.id, day >= start)
        .group_by(day)
        .order_by(day)
    )
    total = db.scalar(
        select(func.count()).select_from(Submission).where(Submission.student_id == user.id)
    )
    best = (
        select(Submission.assignment_id, func.max(Submission.score).label("best"))
        .where(Submission.student_id == user.id)
        .group_by(Submission.assignment_id)
        .subquery()
    )
    solved = db.scalar(select(func.count()).select_from(best).where(best.c.best == 100))
    return Activity(
        weeks=weeks,
        days=[ActivityDay(date=row.day, count=row.count) for row in rows],
        totals=ActivityTotals(submissions=total, solved=solved, concepts_mastered=0),
    )
