from typing import Literal

from pydantic import BaseModel

from app.models.submission import Verdict

Level = Literal["review", "progress", "mastered"]


class ConceptTest(BaseModel):
    """One test that checks the concept, as it went in the counted submission."""

    __test__ = False

    assignment_id: int
    assignment_title: str
    test_case_id: int
    test_name: str  # hidden tests: "Hidden test #n" for students
    is_hidden: bool
    verdict: Verdict


class ConceptStat(BaseModel):
    concept_id: int
    concept: str
    total: int  # tests that check this concept
    passed: int
    pass_rate: float  # 0..1
    level: Level
    assignment_count: int
    tests: list[ConceptTest]  # in assignment order, then test order


class Thresholds(BaseModel):
    review_below: float
    mastered_from: float


class StudentConceptReport(BaseModel):
    course_id: int
    course_title: str
    assignment_count: int  # assignments with a counted submission
    tests_total: int  # distinct tests across those submissions
    tests_passed: int
    verdicts: list[Verdict]  # one square per test, for the summary row
    concepts: list[ConceptStat]  # weakest first
    thresholds: Thresholds


class ClassConceptStat(BaseModel):
    concept_id: int
    concept: str
    average_pass_rate: float  # mean of the students' own pass rates
    level: Level
    students_with_data: int
    students_in_review: int
    students_mastered: int


class ClassConceptReport(BaseModel):
    course_id: int
    course_title: str
    students: int  # enrolled
    students_with_data: int  # enrolled students with at least one counted submission
    concepts: list[ClassConceptStat]  # weakest first
    thresholds: Thresholds
