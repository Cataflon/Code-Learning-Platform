"""Aggregates checked against numbers worked out by hand from a small, known class.

The class: three students, two assignments.

"Digit sum" has 4 tests (weight 1 each): t1, t2, t3, t4.
    Ana    attempt 1: P P F F  -> 50      attempt 2: P P P F -> 75   (best 75)
    Bogdan attempt 1: P P P P  -> 100                                (best 100)
    Carmen attempt 1: F F F F  -> 0       attempt 2: P F F F -> 25   (best 25)
"Binary search" has 2 tests:
    Ana    attempt 1: P P      -> 100
    Bogdan, Carmen: nothing
"""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.models import Enrollment, Role, SubmissionStatus
from app.services import dashboard_service
from app.services.dashboard_service import score_distribution

P, F = True, False


@pytest.fixture
def school(make_user, make_course, make_assignment, make_test_case, make_submission, make_concept):
    teacher = make_user(Role.teacher)
    ana, bogdan, carmen = (
        make_user(Role.student, full_name=name) for name in ("Ana Pop", "Bogdan Rus", "Carmen Dan")
    )
    course = make_course(teacher, students=[ana, bogdan, carmen], color="blue")
    loops = make_concept(course, "Loops")
    digit_sum = make_assignment(
        course, title="Digit sum", due_at=datetime.now(UTC) + timedelta(days=1)
    )
    for index in range(4):
        make_test_case(
            digit_sum,
            name=f"t{index + 1}",
            is_hidden=index == 3,
            concepts=[loops] if index == 0 else [],
        )
    binary = make_assignment(
        course, title="Binary search", due_at=datetime.now(UTC) + timedelta(days=5)
    )
    for index in range(2):
        make_test_case(binary, name=f"b{index + 1}")

    t0 = datetime.now(UTC) - timedelta(hours=5)
    make_submission(ana, digit_sum, [P, P, F, F], created_at=t0)
    make_submission(ana, digit_sum, [P, P, P, F], created_at=t0 + timedelta(hours=1))
    make_submission(bogdan, digit_sum, [P, P, P, P], created_at=t0 + timedelta(hours=2))
    make_submission(carmen, digit_sum, [F, F, F, F], created_at=t0 + timedelta(hours=3))
    make_submission(carmen, digit_sum, [P, F, F, F], created_at=t0 + timedelta(hours=4))
    make_submission(ana, binary, [P, P], created_at=t0 + timedelta(hours=4, minutes=30))
    return {
        "teacher": teacher,
        "ana": ana,
        "bogdan": bogdan,
        "carmen": carmen,
        "course": course,
        "digit_sum": digit_sum,
        "binary": binary,
    }


def test_student_dashboard_has_best_score_and_latest_squares(db_session, school):
    dashboard = dashboard_service.student_dashboard(db_session, school["ana"])

    by_title = {item.title: item for item in dashboard.assignments}
    digit_sum = by_title["Digit sum"]
    assert [item.title for item in dashboard.assignments] == [
        "Digit sum",
        "Binary search",
    ]  # by due
    assert digit_sum.best_score == 75
    assert digit_sum.attempts_used == 2
    assert [v.value for v in digit_sum.last_verdicts] == [
        "passed",
        "passed",
        "passed",
        "wrong_answer",
    ]
    assert digit_sum.course_color == "blue"
    assert by_title["Binary search"].best_score == 100
    assert dashboard.stats.to_submit == 1  # Digit sum is open and below 100
    assert dashboard.stats.average_best_score == 88  # (75 + 100) / 2 = 87.5
    assert [s.assignment_title for s in dashboard.recent_submissions] == [
        "Binary search",
        "Digit sum",
        "Digit sum",
    ]
    assert dashboard.recent_submissions[0].score == 100


def test_student_dashboard_for_a_student_without_submissions(db_session, school):
    dashboard = dashboard_service.student_dashboard(db_session, school["bogdan"])
    binary = next(item for item in dashboard.assignments if item.title == "Binary search")

    assert binary.best_score is None
    assert binary.last_verdicts == []
    assert binary.attempts_used == 0
    assert dashboard.stats.to_submit == 1  # Binary search; Digit sum is already at 100
    assert dashboard.stats.average_best_score == 100


def test_dashboard_hides_drafts_and_other_courses(db_session, school, make_course, make_assignment):
    make_assignment(school["course"], title="Draft", is_published=False)
    make_assignment(make_course(), title="Other course")

    dashboard = dashboard_service.student_dashboard(db_session, school["ana"])

    assert {item.title for item in dashboard.assignments} == {"Digit sum", "Binary search"}
    assert [course.title for course in dashboard.courses] == ["Procedural Programming"]


def test_assignment_stats_match_hand_computed_values(db_session, school):
    stats = dashboard_service.assignment_stats(db_session, school["digit_sum"])

    assert stats.submission_count == 5
    assert stats.submitted_count == 3
    assert stats.enrolled_count == 3
    assert stats.running_count == 0
    assert stats.average_score == 67  # best scores 75, 100, 25 -> 66.67
    # Best submissions: Ana PPPF, Bogdan PPPP, Carmen PFFF
    assert [(test.name, test.passed, test.total) for test in stats.tests] == [
        ("t1", 3, 3),
        ("t2", 2, 3),
        ("t3", 2, 3),
        ("t4", 1, 3),
    ]
    assert stats.tests[3].pass_rate == pytest.approx(1 / 3)
    assert stats.tests[3].is_hidden is True
    assert stats.tests[0].concepts == ["Loops"]
    assert {bucket.label: bucket.count for bucket in stats.score_distribution} == {
        "0–25%": 1,
        "26–50%": 0,
        "51–75%": 1,
        "76–99%": 0,
        "100%": 1,
    }


def test_assignment_stats_count_running_and_ignore_students_who_left(
    db_session, school, make_submission
):
    make_submission(school["bogdan"], school["digit_sum"], status=SubmissionStatus.running)
    db_session.delete(db_session.get(Enrollment, (school["carmen"].id, school["course"].id)))
    db_session.commit()

    stats = dashboard_service.assignment_stats(db_session, school["digit_sum"])

    assert stats.running_count == 1
    assert stats.enrolled_count == 2
    assert stats.submitted_count == 2  # Carmen left the course
    assert stats.submission_count == 4  # 2 of Ana + 2 of Bogdan
    assert stats.average_score == 88  # 75 and 100


def test_assignment_stats_without_submissions(db_session, school, make_assignment, make_test_case):
    empty = make_assignment(school["course"], title="Empty")
    make_test_case(empty)

    stats = dashboard_service.assignment_stats(db_session, empty)

    assert stats.submission_count == 0
    assert stats.average_score is None
    assert stats.tests[0].pass_rate is None
    assert sum(bucket.count for bucket in stats.score_distribution) == 0


def test_score_distribution_boundaries():
    buckets = {b.label: b.count for b in score_distribution([0, 25, 26, 50, 51, 75, 76, 99, 100])}

    assert buckets == {"0–25%": 2, "26–50%": 2, "51–75%": 2, "76–99%": 2, "100%": 1}


def test_assignment_overview_buckets_students_by_best_result(db_session, school):
    overview = dashboard_service.assignment_overview(db_session, school["course"])

    submitted, buckets = overview[school["digit_sum"].id]
    assert submitted == 3
    assert (buckets.full, buckets.partial, buckets.none) == (1, 2, 0)  # 100 | 75, 25 | -
    assert overview[school["binary"].id][0] == 1


def test_course_stats(db_session, school):
    stats = dashboard_service.course_stats(db_session, school["course"])

    assert stats.students == 3
    assert stats.submissions_today >= 0
    assert stats.average_score == 75  # best per (student, assignment): 75, 100, 25, 100


def test_search_filters_counts_and_pagination(db_session, school):
    teacher, digit_sum = school["teacher"], school["digit_sum"]

    everything = dashboard_service.search_submissions(db_session, digit_sum, teacher, page_size=2)
    partial = dashboard_service.search_submissions(
        db_session, digit_sum, teacher, verdict="partial"
    )
    wrong = dashboard_service.search_submissions(db_session, digit_sum, teacher, verdict="wrong")
    second_page = dashboard_service.search_submissions(
        db_session, digit_sum, teacher, page=2, page_size=2
    )

    assert everything.total == 5
    assert len(everything.items) == 2
    assert everything.counts.model_dump() == {
        "all": 5,
        "correct": 1,
        "partial": 3,
        "wrong": 1,
        "running": 0,
    }
    assert sorted(item.score for item in partial.items) == [25, 50, 75]
    assert partial.total == 3
    assert [item.score for item in wrong.items] == [0]
    assert [item.student_name for item in everything.items] == ["Carmen Dan", "Carmen Dan"]
    assert [item.student_name for item in second_page.items] == ["Bogdan Rus", "Ana Pop"]


def test_search_by_student_name_treats_wildcards_literally(db_session, school):
    teacher, digit_sum = school["teacher"], school["digit_sum"]

    by_name = dashboard_service.search_submissions(db_session, digit_sum, teacher, q="ana")
    wildcard = dashboard_service.search_submissions(db_session, digit_sum, teacher, q="%")

    assert {item.student_name for item in by_name.items} == {"Ana Pop"}
    assert by_name.counts.all == 2
    assert wildcard.total == 0


def test_search_as_student_returns_only_own_attempts(db_session, school):
    page = dashboard_service.search_submissions(
        db_session, school["digit_sum"], school["ana"], q="Bogdan"
    )

    assert page.total == 2
    assert {item.student_name for item in page.items} == {"Ana Pop"}  # q is ignored for students


def test_user_activity_groups_by_day_and_counts_totals(db_session, school, make_submission):
    ana, digit_sum = school["ana"], school["digit_sum"]
    today = datetime.now(UTC).date()
    old_day = datetime.now(UTC) - timedelta(days=10)
    make_submission(ana, digit_sum, [P, P, P, P], created_at=old_day)
    make_submission(
        ana, digit_sum, [F, F, F, F], created_at=datetime.now(UTC) - timedelta(days=200)
    )

    activity = dashboard_service.user_activity(db_session, ana, weeks=14, today=today)

    by_day = {day.date: day.count for day in activity.days}
    assert by_day[old_day.date()] == 1
    assert sum(by_day.values()) == 4  # the one from 200 days ago is outside the window
    assert activity.totals.submissions == 5
    assert activity.totals.solved == 2  # both assignments have a 100 now
    assert all(isinstance(day, date) for day in by_day)
