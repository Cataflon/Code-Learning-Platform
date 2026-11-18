"""Import every model here so Base.metadata (and Alembic) sees all tables."""

from app.models.assignment import Assignment, TestCase, test_case_concepts
from app.models.course import COURSE_COLORS, Concept, Course, Enrollment
from app.models.generation import GenerationJob, MaterialPage, ReviewStatus, TestSource
from app.models.material import (
    AssignmentMaterial,
    FileType,
    Material,
    MaterialCategory,
    TestCaseMaterial,
)
from app.models.submission import Submission, SubmissionStatus, TestResult, Verdict
from app.models.user import InviteCode, Role, User

__all__ = [
    "COURSE_COLORS",
    "Assignment",
    "AssignmentMaterial",
    "Concept",
    "Course",
    "Enrollment",
    "FileType",
    "GenerationJob",
    "InviteCode",
    "Material",
    "MaterialCategory",
    "MaterialPage",
    "ReviewStatus",
    "Role",
    "Submission",
    "SubmissionStatus",
    "TestCase",
    "TestCaseMaterial",
    "TestResult",
    "TestSource",
    "User",
    "Verdict",
    "test_case_concepts",
]
