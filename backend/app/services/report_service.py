"""The "where you go wrong" report: test verdicts turned into concepts to review.

The work is split in two on purpose:

* ``fetch_concept_rows`` is the only function that talks to the database. It returns raw rows,
  one per (concept, test result) pair of the submissions that count.
* ``classify``, ``aggregate_concepts`` and ``aggregate_class`` are pure functions over those
  rows, so the counting rules are tested with hand-written lists, without a database.

Which submission counts (decision D17): for every student and assignment, the most recent
finished (``done``) submission. Earlier mistakes do not count against the student, and
submissions that ended in ``error`` are ignored. Only published assignments and students who
are still enrolled are included.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    Assignment,
    Concept,
    Course,
    Enrollment,
    ReviewStatus,
    Submission,
    SubmissionStatus,
    TestCase,
    TestResult,
    User,
    Verdict,
    test_case_concepts,
)
from app.schemas.report import (
    ClassConceptReport,
    ClassConceptStat,
    ConceptStat,
    ConceptTest,
    Level,
    StudentConceptReport,
    Thresholds,
)


@dataclass(frozen=True)
class ConceptRow:
    """One concept of one test, with the verdict that test got in a counted submission."""

    student_id: int
    concept_id: int
    concept: str
    assignment_id: int
    assignment_title: str
    assignment_order: int  # position of the assignment in the course (for sorting)
    test_case_id: int
    test_name: str
    test_position: int
    is_hidden: bool
    verdict: Verdict


# --- pure functions --------------------------------------------------------------------------


def thresholds() -> Thresholds:
    settings = get_settings()
    return Thresholds(
        review_below=settings.concept_review_below,
        mastered_from=settings.concept_mastered_from,
    )


def classify(pass_rate: float, limits: Thresholds | None = None) -> Level:
    """Below 50%: review; from 50% to below 80%: progress; from 80%: mastered."""
    limits = limits or thresholds()
    if pass_rate < limits.review_below:
        return "review"
    if pass_rate < limits.mastered_from:
        return "progress"
    return "mastered"


def aggregate_concepts(
    rows: Iterable[ConceptRow], limits: Thresholds | None = None
) -> list[ConceptStat]:
    """Statistics per concept for ONE student, weakest first.

    Every test counts once per concept it is tagged with, so a test with two concepts
    counts towards both. Weights do not matter here: the rate is passed tests / tests.
    """
    limits = limits or thresholds()
    by_concept: dict[int, list[ConceptRow]] = defaultdict(list)
    for row in rows:
        by_concept[row.concept_id].append(row)

    stats = []
    for concept_id, concept_rows in by_concept.items():
        ordered = sorted(
            concept_rows, key=lambda r: (r.assignment_order, r.assignment_id, r.test_position)
        )
        total = len(ordered)
        passed = sum(1 for r in ordered if r.verdict == Verdict.passed)
        rate = passed / total
        stats.append(
            ConceptStat(
                concept_id=concept_id,
                concept=ordered[0].concept,
                total=total,
                passed=passed,
                pass_rate=rate,
                level=classify(rate, limits),
                assignment_count=len({r.assignment_id for r in ordered}),
                tests=[
                    ConceptTest(
                        assignment_id=r.assignment_id,
                        assignment_title=r.assignment_title,
                        test_case_id=r.test_case_id,
                        test_name=r.test_name,
                        is_hidden=r.is_hidden,
                        verdict=r.verdict,
                    )
                    for r in ordered
                ],
            )
        )
    stats.sort(key=lambda s: (s.pass_rate, s.concept.lower()))
    return stats


def aggregate_class(
    rows: Iterable[ConceptRow], limits: Thresholds | None = None
) -> list[ClassConceptStat]:
    """Per concept, over the students who have data: their average rate and their levels."""
    limits = limits or thresholds()
    by_student: dict[int, list[ConceptRow]] = defaultdict(list)
    for row in rows:
        by_student[row.student_id].append(row)

    per_concept: dict[int, list[ConceptStat]] = defaultdict(list)
    for student_rows in by_student.values():
        for stat in aggregate_concepts(student_rows, limits):
            per_concept[stat.concept_id].append(stat)

    result = []
    for concept_id, stats in per_concept.items():
        average = sum(s.pass_rate for s in stats) / len(stats)
        result.append(
            ClassConceptStat(
                concept_id=concept_id,
                concept=stats[0].concept,
                average_pass_rate=average,
                level=classify(average, limits),
                students_with_data=len(stats),
                students_in_review=sum(1 for s in stats if s.level == "review"),
                students_mastered=sum(1 for s in stats if s.level == "mastered"),
            )
        )
    result.sort(key=lambda s: (s.average_pass_rate, s.concept.lower()))
    return result


# --- the query -------------------------------------------------------------------------------


def _counted_submissions(course_id: int, student_id: int | None):
    """The latest finished submission of each (enrolled student, published assignment).

    ``DISTINCT ON (student_id, assignment_id)`` keeps the first row of each pair in the
    ORDER BY, which is the newest one.
    """
    query = (
        select(Submission.id)
        .join(Assignment, Assignment.id == Submission.assignment_id)
        .join(
            Enrollment,
            and_(
                Enrollment.user_id == Submission.student_id,
                Enrollment.course_id == Assignment.course_id,
            ),
        )
        .where(
            Assignment.course_id == course_id,
            Assignment.is_published.is_(True),
            Submission.status == SubmissionStatus.done,
        )
        .ext(distinct_on(Submission.student_id, Submission.assignment_id))
        .order_by(
            Submission.student_id,
            Submission.assignment_id,
            Submission.created_at.desc(),
            Submission.id.desc(),
        )
    )
    if student_id is not None:
        query = query.where(Submission.student_id == student_id)
    return query


def fetch_concept_rows(
    db: Session, course_id: int, student_id: int | None = None, mask_hidden: bool = True
) -> list[ConceptRow]:
    """Raw rows for the report. Each join adds one link of the chain:
    submissions -> test_results -> test_cases -> test_case_concepts -> concepts.
    """
    counted = _counted_submissions(course_id, student_id).subquery()
    query = (
        select(
            Submission.student_id,
            Concept.id,
            Concept.name,
            Assignment.id,
            Assignment.title,
            TestCase.id,
            TestCase.name,
            TestCase.position,
            TestCase.is_hidden,
            TestResult.verdict,
        )
        .select_from(TestResult)
        .join(Submission, Submission.id == TestResult.submission_id)
        .join(Assignment, Assignment.id == Submission.assignment_id)
        .join(TestCase, TestCase.id == TestResult.test_case_id)
        .join(test_case_concepts, test_case_concepts.c.test_case_id == TestCase.id)
        .join(Concept, Concept.id == test_case_concepts.c.concept_id)
        .where(TestResult.submission_id.in_(select(counted.c.id)))
    )
    raw = db.execute(query).all()
    if not raw:
        return []

    assignment_ids = {row[3] for row in raw}
    order = _assignment_order(db, assignment_ids)
    labels = _hidden_labels(db, assignment_ids) if mask_hidden else {}
    return [
        ConceptRow(
            student_id=student,
            concept_id=concept_id,
            concept=concept_name,
            assignment_id=assignment_id,
            assignment_title=assignment_title,
            assignment_order=order[assignment_id],
            test_case_id=test_id,
            test_name=labels.get(test_id, test_name),
            test_position=position,
            is_hidden=is_hidden,
            verdict=verdict,
        )
        for (
            student,
            concept_id,
            concept_name,
            assignment_id,
            assignment_title,
            test_id,
            test_name,
            position,
            is_hidden,
            verdict,
        ) in raw
    ]


def _assignment_order(db: Session, assignment_ids: set[int]) -> dict[int, int]:
    """Same order as everywhere else: by deadline (no deadline last), then by id."""
    rows = db.scalars(
        select(Assignment.id)
        .where(Assignment.id.in_(assignment_ids))
        .order_by(Assignment.due_at.nulls_last(), Assignment.id)
    )
    return {assignment_id: index for index, assignment_id in enumerate(rows)}


def _hidden_labels(db: Session, assignment_ids: set[int]) -> dict[int, str]:
    """Hidden tests keep their anonymous name, numbered per assignment like on the results."""
    rows = db.execute(
        select(TestCase.id, TestCase.assignment_id)
        .where(
            TestCase.assignment_id.in_(assignment_ids),
            TestCase.is_hidden.is_(True),
            TestCase.review_status == ReviewStatus.approved,
        )
        .order_by(TestCase.assignment_id, TestCase.position, TestCase.id)
    )
    labels: dict[int, str] = {}
    counters: dict[int, int] = defaultdict(int)
    for test_id, assignment_id in rows:
        counters[assignment_id] += 1
        labels[test_id] = f"Hidden test #{counters[assignment_id]}"
    return labels


# --- reports ---------------------------------------------------------------------------------


def student_concept_report(db: Session, student: User, course: Course) -> StudentConceptReport:
    rows = fetch_concept_rows(db, course.id, student_id=student.id, mask_hidden=True)
    limits = thresholds()
    # The summary counts every test once, even when it has several concepts.
    unique: dict[int, ConceptRow] = {}
    for row in sorted(rows, key=lambda r: (r.assignment_order, r.test_position)):
        unique.setdefault(row.test_case_id, row)
    verdicts = [row.verdict for row in unique.values()]
    return StudentConceptReport(
        course_id=course.id,
        course_title=course.title,
        assignment_count=len({row.assignment_id for row in rows}),
        tests_total=len(verdicts),
        tests_passed=sum(1 for verdict in verdicts if verdict == Verdict.passed),
        verdicts=verdicts,
        concepts=aggregate_concepts(rows, limits),
        thresholds=limits,
    )


def class_concept_report(db: Session, course: Course) -> ClassConceptReport:
    rows = fetch_concept_rows(db, course.id, mask_hidden=False)
    limits = thresholds()
    return ClassConceptReport(
        course_id=course.id,
        course_title=course.title,
        students=len(course.enrollments),
        students_with_data=len({row.student_id for row in rows}),
        concepts=aggregate_class(rows, limits),
        thresholds=limits,
    )


def student_concepts_everywhere(db: Session, student: User) -> list[ConceptStat]:
    """The student's concepts in every course they are enrolled in (dashboard and profile)."""
    courses = db.scalars(
        select(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.user_id == student.id)
    )
    limits = thresholds()
    stats: list[ConceptStat] = []
    for course in courses:
        rows = fetch_concept_rows(db, course.id, student_id=student.id, mask_hidden=True)
        stats.extend(aggregate_concepts(rows, limits))
    return stats
