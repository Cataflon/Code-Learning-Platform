"""Shared FastAPI dependencies.

Step 1 has no real authentication: ``get_current_user`` is a stand-in that returns a seeded
user, and the ``*_for_member`` / ``*_for_owner`` loaders only fetch the resource. Step 2
replaces their bodies with real token and access checks; the routers do not change.
"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import UnauthorizedError
from app.db.session import get_db
from app.models import Assignment, Course, Role, TestCase, User
from app.services import assignment_service, course_service, test_case_service

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession, x_debug_user_id: Annotated[int | None, Header()] = None
) -> User:
    """Stand-in: the user named by X-Debug-User-Id, or the first seeded teacher."""
    if x_debug_user_id is not None:
        user = db.get(User, x_debug_user_id)
    else:
        user = db.scalar(select(User).where(User.role == Role.teacher).order_by(User.id))
    if user is None:
        raise UnauthorizedError("No user available; run scripts/seed.py first")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
TeacherUser = CurrentUser
StudentUser = CurrentUser


def get_course_for_member(course_id: int, db: DbSession) -> Course:
    return course_service.get_course(db, course_id)


def get_course_for_owner(course_id: int, db: DbSession) -> Course:
    return course_service.get_course(db, course_id)


def get_assignment_for_member(assignment_id: int, db: DbSession) -> Assignment:
    return assignment_service.get_assignment(db, assignment_id)


def get_assignment_for_owner(assignment_id: int, db: DbSession) -> Assignment:
    return assignment_service.get_assignment(db, assignment_id)


def get_test_case_for_owner(test_case_id: int, db: DbSession) -> TestCase:
    return test_case_service.get_test_case(db, test_case_id)


MemberCourse = Annotated[Course, Depends(get_course_for_member)]
OwnedCourse = Annotated[Course, Depends(get_course_for_owner)]
MemberAssignment = Annotated[Assignment, Depends(get_assignment_for_member)]
OwnedAssignment = Annotated[Assignment, Depends(get_assignment_for_owner)]
OwnedTestCase = Annotated[TestCase, Depends(get_test_case_for_owner)]
