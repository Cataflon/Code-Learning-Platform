from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import (
    CurrentUser,
    DbSession,
    MemberCourse,
    OwnedCourse,
    StudentUser,
    TeacherUser,
)
from app.schemas.course import (
    CourseCreate,
    CourseRead,
    CourseUpdate,
    JoinCourseRequest,
    StudentRead,
)
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["courses"])

Limit = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0)]


@router.get("", response_model=list[CourseRead])
def list_courses(db: DbSession, user: CurrentUser, limit: Limit = 50, offset: Offset = 0):
    courses = course_service.list_courses_for(db, user, limit, offset)
    return [CourseRead.for_viewer(course, user) for course in courses]


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate, db: DbSession, user: TeacherUser):
    return CourseRead.for_viewer(course_service.create_course(db, user, data), user)


# Declared before /{course_id} so "join" is not parsed as an id.
@router.post("/join", response_model=CourseRead)
def join_course(data: JoinCourseRequest, db: DbSession, user: StudentUser):
    return CourseRead.for_viewer(course_service.join_course(db, user, data.join_code), user)


@router.get("/{course_id}", response_model=CourseRead)
def get_course(course: MemberCourse, user: CurrentUser):
    return CourseRead.for_viewer(course, user)


@router.patch("/{course_id}", response_model=CourseRead)
def update_course(data: CourseUpdate, course: OwnedCourse, db: DbSession, user: CurrentUser):
    return CourseRead.for_viewer(course_service.update_course(db, course, data), user)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course: OwnedCourse, db: DbSession) -> None:
    course_service.delete_course(db, course)


@router.get("/{course_id}/students", response_model=list[StudentRead])
def list_students(course: OwnedCourse, db: DbSession, limit: Limit = 100, offset: Offset = 0):
    return course_service.list_students(db, course, limit, offset)
