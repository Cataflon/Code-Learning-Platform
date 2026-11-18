from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models import FileType, MaterialCategory


class MaterialUsage(BaseModel):
    """An assignment that points to the material, directly or through some of its tests."""

    assignment_id: int
    assignment_title: str
    for_assignment: bool  # linked to the whole assignment
    test_count: int  # tests of that assignment linked to the material


class MaterialRead(BaseModel):
    id: int
    course_id: int
    title: str
    category: MaterialCategory
    file_type: FileType
    original_filename: str
    size_bytes: int
    page_count: int
    created_at: datetime
    used_in: list[MaterialUsage] = []


class MaterialUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    category: MaterialCategory | None = None

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = " ".join(value.split())
        if not value:
            raise ValueError("must not be empty")
        return value


class MaterialLinkIn(BaseModel):
    material_id: int
    pages: str = Field(default="", max_length=200)  # "12-15, 18"; empty = the whole material


class MaterialLinkRead(BaseModel):
    material_id: int
    title: str
    category: MaterialCategory
    file_type: FileType
    page_count: int
    pages: str
    first_page: int


class LearnCourse(BaseModel):
    id: int
    title: str
    color: str
    teacher_name: str
    material_count: int
    last_material_at: datetime | None


class FailedTest(BaseModel):
    test_case_id: int
    name: str  # hidden tests: "Hidden test #n"
    is_hidden: bool
    concepts: list[str]


class Recommendation(BaseModel):
    material_id: int
    title: str
    category: MaterialCategory
    file_type: FileType
    page_count: int
    pages: str  # merged pages of every failed test that points here; "" = whole material
    first_page: int
    test_count: int  # failed tests that need this material
    tests: list[str]  # their names
    from_assignment: bool  # chosen through the assignment because the tests had none


class RecommendationsRead(BaseModel):
    submission_id: int
    assignment_id: int
    failed_tests: list[FailedTest]
    materials: list[Recommendation]
