"""The counting rules of the concept report, on hand-written rows (no database)."""

import pytest

from app.models import Verdict
from app.schemas.report import Thresholds
from app.services.report_service import ConceptRow, aggregate_class, aggregate_concepts, classify

LIMITS = Thresholds(review_below=0.5, mastered_from=0.8)
P, F = Verdict.passed, Verdict.wrong_answer


def row(concept, test_id, verdict, student=1, assignment=1, position=None):
    concept_id = {"Recursion": 1, "Lists": 2, "Loops": 3}[concept]
    return ConceptRow(
        student_id=student,
        concept_id=concept_id,
        concept=concept,
        assignment_id=assignment,
        assignment_title=f"Assignment {assignment}",
        assignment_order=assignment,
        test_case_id=test_id,
        test_name=f"t{test_id}",
        test_position=position if position is not None else test_id,
        is_hidden=False,
        verdict=verdict,
    )


@pytest.mark.parametrize(
    ("rate", "level"),
    [
        (0.0, "review"),
        (0.49, "review"),
        (0.5, "progress"),
        (0.79, "progress"),
        (0.8, "mastered"),
        (1.0, "mastered"),
    ],
)
def test_classify_boundaries(rate, level):
    assert classify(rate, LIMITS) == level


def test_student_good_at_recursion_and_weak_at_lists():
    rows = [
        row("Recursion", 1, P),
        row("Recursion", 2, P),
        row("Recursion", 3, P, assignment=2),
        row("Lists", 4, F, assignment=2),
        row("Lists", 5, P, assignment=2),
        row("Lists", 6, F, assignment=3),
    ]

    stats = aggregate_concepts(rows, LIMITS)

    lists, recursion = stats  # weakest first
    assert (lists.concept, lists.passed, lists.total, lists.level) == ("Lists", 1, 3, "review")
    assert lists.pass_rate == pytest.approx(1 / 3)
    assert lists.assignment_count == 2
    assert (recursion.concept, recursion.passed, recursion.total) == ("Recursion", 3, 3)
    assert recursion.level == "mastered"
    assert recursion.assignment_count == 2


def test_a_test_with_two_concepts_counts_for_both():
    rows = [row("Recursion", 1, F), row("Lists", 1, F), row("Lists", 2, P)]

    stats = {s.concept: s for s in aggregate_concepts(rows, LIMITS)}

    assert (stats["Recursion"].passed, stats["Recursion"].total) == (0, 1)
    assert (stats["Lists"].passed, stats["Lists"].total) == (1, 2)


def test_tests_are_listed_in_assignment_then_test_order():
    rows = [
        row("Loops", 9, F, assignment=2, position=1),
        row("Loops", 7, P, assignment=1, position=2),
        row("Loops", 8, P, assignment=1, position=1),
    ]

    (loops,) = aggregate_concepts(rows, LIMITS)

    assert [test.test_case_id for test in loops.tests] == [8, 7, 9]
    assert loops.level == "progress"  # 2 of 3


def test_empty_input_gives_empty_report():
    assert aggregate_concepts([], LIMITS) == []
    assert aggregate_class([], LIMITS) == []


def test_class_average_uses_each_students_own_rate():
    rows = [
        # student 1: Lists 1 of 1 (100%), student 2: Lists 0 of 3 (0%), student 3: Lists 1 of 2
        row("Lists", 1, P, student=1),
        row("Lists", 1, F, student=2),
        row("Lists", 2, F, student=2),
        row("Lists", 3, F, student=2),
        row("Lists", 1, P, student=3),
        row("Lists", 2, F, student=3),
        # only student 1 has Recursion data
        row("Recursion", 4, P, student=1),
    ]

    stats = {s.concept: s for s in aggregate_class(rows, LIMITS)}

    lists = stats["Lists"]
    assert lists.average_pass_rate == pytest.approx((1 + 0 + 0.5) / 3)
    assert lists.level == "progress"  # exactly 50% is already "in progress"
    assert (lists.students_with_data, lists.students_in_review, lists.students_mastered) == (
        3,
        1,
        1,
    )
    assert stats["Recursion"].students_with_data == 1
    assert [s.concept for s in aggregate_class(rows, LIMITS)] == ["Lists", "Recursion"]
