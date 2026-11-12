from datetime import datetime

from pydantic import BaseModel, Field

from app.models.submission import SubmissionStatus, Verdict

MAX_CODE_BYTES = 64 * 1024


class SubmissionCreate(BaseModel):
    code: str = Field(min_length=1, max_length=MAX_CODE_BYTES)


class TestResultRead(BaseModel):
    """One test in a submission. For a student, hidden tests come without any content."""

    __test__ = False

    test_case_id: int
    name: str
    position: int
    is_hidden: bool
    verdict: Verdict | None  # None while the test has not run yet
    runtime_ms: int | None
    concepts: list[str]
    hint: str | None = None  # only when the test failed
    input_data: str | None = None
    expected_output: str | None = None
    actual_output: str | None = None
    stderr: str | None = None


class SubmissionSummary(BaseModel):
    """List item: no code and no per-test details, only the verdict squares."""

    id: int
    assignment_id: int
    student_id: int
    student_name: str
    attempt_number: int
    status: SubmissionStatus
    score: int | None
    passed_count: int
    total_count: int
    verdicts: list[Verdict | None]  # in test order
    error_excerpt: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class SubmissionRead(SubmissionSummary):
    code: str
    error_message: str | None
    results: list[TestResultRead]
