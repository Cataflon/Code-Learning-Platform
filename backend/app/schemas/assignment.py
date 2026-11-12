from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.course import ConceptRead


class ResultBuckets(BaseModel):
    """Students by their best result on an assignment."""

    full: int = 0  # passed every test
    partial: int = 0
    none: int = 0


MAX_TEXT = 64 * 1024  # 64 KB for test input/output


class AssignmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=20000)
    time_limit_ms: int = Field(default=2000, ge=100, le=10000)
    memory_limit_mb: int = Field(default=128, ge=16, le=512)
    due_at: datetime | None = None
    is_published: bool = False
    max_submissions: int = Field(default=10, ge=1, le=100)


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    time_limit_ms: int | None = Field(default=None, ge=100, le=10000)
    memory_limit_mb: int | None = Field(default=None, ge=16, le=512)
    due_at: datetime | None = None
    is_published: bool | None = None
    max_submissions: int | None = Field(default=None, ge=1, le=100)


class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    course_title: str
    title: str
    description: str
    language: str
    time_limit_ms: int
    memory_limit_mb: int
    due_at: datetime | None
    is_published: bool
    max_submissions: int
    status: str  # draft | open | closed
    test_count: int
    hidden_test_count: int
    created_at: datetime
    # Filled in only for the student who is asking.
    submissions_left: int | None = None
    # Filled in only for the course teacher, in the course's assignment list.
    submitted_count: int | None = None
    enrolled_count: int | None = None
    result_buckets: ResultBuckets | None = None


class TestCaseCreate(BaseModel):
    __test__ = False

    name: str = Field(min_length=1, max_length=120)
    input_data: str = Field(default="", max_length=MAX_TEXT)
    expected_output: str = Field(default="", max_length=MAX_TEXT)
    is_hidden: bool = False
    weight: int = Field(default=1, ge=1, le=100)
    position: int | None = Field(default=None, ge=0)  # None = append at the end
    hint: str | None = Field(default=None, max_length=500)
    concept_ids: list[int] = Field(default_factory=list, max_length=20)


class TestCaseUpdate(BaseModel):
    __test__ = False

    name: str | None = Field(default=None, min_length=1, max_length=120)
    input_data: str | None = Field(default=None, max_length=MAX_TEXT)
    expected_output: str | None = Field(default=None, max_length=MAX_TEXT)
    is_hidden: bool | None = None
    weight: int | None = Field(default=None, ge=1, le=100)
    position: int | None = Field(default=None, ge=0)
    hint: str | None = Field(default=None, max_length=500)
    concept_ids: list[int] | None = Field(default=None, max_length=20)


class TestCaseRead(BaseModel):
    """Full view, for the course teacher."""

    __test__ = False
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    name: str
    input_data: str
    expected_output: str
    is_hidden: bool
    weight: int
    position: int
    hint: str | None
    concepts: list[ConceptRead]


class TestCasePublicRead(BaseModel):
    """What a student sees: public tests only, without weight or hint."""

    __test__ = False
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    name: str
    input_data: str
    expected_output: str
    position: int
    concepts: list[ConceptRead]
