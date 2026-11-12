from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Course, Role, User

CourseColor = Literal["indigo", "blue", "purple", "green", "amber", "rose"]


def _clean(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be empty")
    return value


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    color: CourseColor = "indigo"

    _clean_title = field_validator("title")(_clean)


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    color: CourseColor | None = None
    regenerate_join_code: bool = False


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    color: str
    teacher_id: int
    teacher_name: str
    join_code: str | None  # only the course teacher sees it
    assignment_count: int = 0
    created_at: datetime

    @classmethod
    def for_viewer(cls, course: Course, viewer: User) -> "CourseRead":
        read = cls.model_validate(course)
        is_teacher = viewer.role == Role.teacher
        if not is_teacher:
            read.join_code = None
        read.assignment_count = sum(
            1 for assignment in course.assignments if is_teacher or assignment.is_published
        )
        return read


class JoinCourseRequest(BaseModel):
    join_code: str = Field(min_length=1, max_length=16)


class StudentRead(BaseModel):
    id: int
    full_name: str
    email: str
    enrolled_at: datetime


class ConceptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)

    _clean_name = field_validator("name")(_clean)


class ConceptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
