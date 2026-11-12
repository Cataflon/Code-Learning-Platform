"""Import every model here so Base.metadata (and Alembic) sees all tables."""

from app.models.assignment import Assignment, TestCase, test_case_concepts
from app.models.course import COURSE_COLORS, Concept, Course, Enrollment
from app.models.submission import Submission, SubmissionStatus, TestResult, Verdict
from app.models.user import Role, User

__all__ = [
    "COURSE_COLORS",
    "Assignment",
    "Concept",
    "Course",
    "Enrollment",
    "Role",
    "Submission",
    "SubmissionStatus",
    "TestCase",
    "TestResult",
    "User",
    "Verdict",
    "test_case_concepts",
]
