"""Shared FastAPI dependencies: the database session, the current user and access checks.

Access rules live here and in the services, never in router bodies:

* no or bad token                         -> 401
* wrong role for the route                -> 403
* a resource of a course you are not in   -> 404 (so its existence is not revealed)
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, PermissionDeniedError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models import Assignment, Course, Role, Submission, TestCase, User
from app.services import (
    assignment_service,
    course_service,
    submission_service,
    test_case_service,
)

DbSession = Annotated[Session, Depends(get_db)]

# auto_error=False so a missing token goes through our uniform 401 response.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

_BEARER = {"WWW-Authenticate": "Bearer"}


def get_current_user(db: DbSession, token: Annotated[str | None, Depends(oauth2_scheme)]) -> User:
    if not token:
        raise UnauthorizedError("Not authenticated", headers=_BEARER)
    payload = decode_token(token)
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Invalid authentication token", headers=_BEARER) from exc
    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("This account no longer exists", headers=_BEARER)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(role: Role) -> Callable[[User], User]:
    def checker(user: CurrentUser) -> User:
        if user.role != role:
            raise PermissionDeniedError(f"Only {role.value}s can do this")
        return user

    return checker


TeacherUser = Annotated[User, Depends(require_role(Role.teacher))]
StudentUser = Annotated[User, Depends(require_role(Role.student))]


def get_course_for_member(course_id: int, db: DbSession, user: CurrentUser) -> Course:
    """The course, if the user teaches it or is enrolled in it."""
    course = course_service.get_course(db, course_id)
    if not course_service.is_member(db, user, course):
        raise NotFoundError("Course not found")
    return course


def get_course_for_owner(course_id: int, db: DbSession, user: TeacherUser) -> Course:
    """The course, if the user is its teacher."""
    course = course_service.get_course(db, course_id)
    if course.teacher_id != user.id:
        raise NotFoundError("Course not found")
    return course


def get_assignment_for_member(assignment_id: int, db: DbSession, user: CurrentUser) -> Assignment:
    assignment = assignment_service.get_assignment(db, assignment_id)
    if not course_service.is_member(db, user, assignment.course):
        raise NotFoundError("Assignment not found")
    # Drafts do not exist as far as students are concerned.
    if user.role == Role.student and not assignment.is_published:
        raise NotFoundError("Assignment not found")
    return assignment


def get_assignment_for_owner(assignment_id: int, db: DbSession, user: TeacherUser) -> Assignment:
    assignment = assignment_service.get_assignment(db, assignment_id)
    if assignment.course.teacher_id != user.id:
        raise NotFoundError("Assignment not found")
    return assignment


def get_test_case_for_owner(test_case_id: int, db: DbSession, user: TeacherUser) -> TestCase:
    test_case = test_case_service.get_test_case(db, test_case_id)
    if test_case.assignment.course.teacher_id != user.id:
        raise NotFoundError("Test case not found")
    return test_case


def get_submission_for_viewer(submission_id: int, db: DbSession, user: CurrentUser) -> Submission:
    """The submission, if the user wrote it or teaches the course it belongs to."""
    submission = submission_service.get_submission(db, submission_id)
    is_author = submission.student_id == user.id
    is_course_teacher = submission.assignment.course.teacher_id == user.id
    if not (is_author or is_course_teacher):
        raise NotFoundError("Submission not found")
    return submission


MemberCourse = Annotated[Course, Depends(get_course_for_member)]
OwnedCourse = Annotated[Course, Depends(get_course_for_owner)]
MemberAssignment = Annotated[Assignment, Depends(get_assignment_for_member)]
OwnedAssignment = Annotated[Assignment, Depends(get_assignment_for_owner)]
OwnedTestCase = Annotated[TestCase, Depends(get_test_case_for_owner)]
ViewableSubmission = Annotated[Submission, Depends(get_submission_for_viewer)]
