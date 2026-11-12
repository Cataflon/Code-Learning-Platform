from datetime import date, datetime

from pydantic import BaseModel

from app.models.submission import SubmissionStatus, Verdict
from app.schemas.submission import SubmissionSummary

# --- student dashboard -----------------------------------------------------------------------


class DashboardCourse(BaseModel):
    id: int
    title: str
    color: str
    teacher_name: str


class DashboardAssignment(BaseModel):
    id: int
    title: str
    course_id: int
    course_title: str
    course_color: str
    due_at: datetime | None
    status: str  # open | closed
    test_count: int
    max_submissions: int
    attempts_used: int
    best_score: int | None  # None = not started
    last_verdicts: list[Verdict | None]  # squares of the latest attempt, in test order
    last_submission_status: SubmissionStatus | None


class DashboardSubmission(BaseModel):
    id: int
    assignment_id: int
    assignment_title: str
    status: SubmissionStatus
    score: int | None
    verdicts: list[Verdict | None]
    created_at: datetime


class ConceptToReview(BaseModel):
    concept: str
    passed: int
    total: int
    verdicts: list[Verdict]


class DashboardStats(BaseModel):
    to_submit: int  # open assignments not yet solved at 100%
    average_best_score: int | None
    concepts_to_review: int


class StudentDashboard(BaseModel):
    stats: DashboardStats
    courses: list[DashboardCourse]
    assignments: list[DashboardAssignment]  # ordered by deadline
    recent_submissions: list[DashboardSubmission]  # the latest five
    concepts_to_review: list[ConceptToReview]  # the weakest three


# --- teacher statistics ----------------------------------------------------------------------


class TestStat(BaseModel):
    __test__ = False

    test_case_id: int
    name: str
    is_hidden: bool
    concepts: list[str]
    passed: int
    total: int
    pass_rate: float | None  # 0..1, None when nobody has run this test


class ScoreBucket(BaseModel):
    label: str
    count: int


class AssignmentStats(BaseModel):
    submission_count: int
    submitted_count: int  # students with at least one submission
    enrolled_count: int
    running_count: int
    average_score: int | None  # average of each student's best score
    tests: list[TestStat]
    score_distribution: list[ScoreBucket]


class CourseStats(BaseModel):
    students: int
    submissions_today: int
    average_score: int | None


# --- submissions list (filters, search, pagination) ------------------------------------------


class SubmissionCounts(BaseModel):
    all: int = 0
    correct: int = 0
    partial: int = 0
    wrong: int = 0
    running: int = 0


class SubmissionPage(BaseModel):
    items: list[SubmissionSummary]
    total: int  # rows matching the current filter
    page: int
    page_size: int
    counts: SubmissionCounts


# --- profile activity ------------------------------------------------------------------------


class ActivityDay(BaseModel):
    date: date
    count: int


class ActivityTotals(BaseModel):
    submissions: int
    solved: int  # assignments solved at 100%
    concepts_mastered: int


class Activity(BaseModel):
    weeks: int
    days: list[ActivityDay]  # only the days that have submissions
    totals: ActivityTotals
