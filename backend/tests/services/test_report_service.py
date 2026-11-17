from datetime import UTC, datetime, timedelta

import pytest

from app.models import Enrollment, Role, SubmissionStatus
from app.services import dashboard_service, report_service

P, F = True, False


@pytest.fixture
def course_setup(make_user, make_course, make_assignment, make_test_case, make_concept):
    teacher = make_user(Role.teacher)
    ana, bogdan = make_user(Role.student), make_user(Role.student)
    course = make_course(teacher, students=[ana, bogdan])
    loops, negative = make_concept(course, "Loops"), make_concept(course, "Negative numbers")
    assignment = make_assignment(course, title="Digit sum")
    make_test_case(assignment, name="Simple", concepts=[loops])
    make_test_case(assignment, name="Zero", concepts=[loops])
    make_test_case(assignment, name="Secret", is_hidden=True, concepts=[loops, negative])
    return {
        "teacher": teacher,
        "ana": ana,
        "bogdan": bogdan,
        "course": course,
        "assignment": assignment,
    }


def stat_of(report, name):
    return next(concept for concept in report.concepts if concept.concept == name)


def test_latest_finished_submission_counts_even_when_worse(
    db_session, course_setup, make_submission
):
    ana, assignment = course_setup["ana"], course_setup["assignment"]
    t0 = datetime.now(UTC) - timedelta(hours=2)
    make_submission(ana, assignment, [P, P, P], created_at=t0)  # old and perfect
    make_submission(ana, assignment, [P, F, F], created_at=t0 + timedelta(hours=1))  # new, worse

    report = report_service.student_concept_report(db_session, ana, course_setup["course"])

    loops = stat_of(report, "Loops")
    assert (loops.passed, loops.total, loops.level) == (1, 3, "review")
    assert (report.tests_passed, report.tests_total, report.assignment_count) == (1, 3, 1)


def test_error_and_running_submissions_are_ignored(db_session, course_setup, make_submission):
    ana, assignment = course_setup["ana"], course_setup["assignment"]
    t0 = datetime.now(UTC) - timedelta(hours=2)
    make_submission(ana, assignment, [P, P, F], created_at=t0)
    make_submission(
        ana, assignment, status=SubmissionStatus.error, created_at=t0 + timedelta(hours=1)
    )
    make_submission(
        ana, assignment, status=SubmissionStatus.running, created_at=t0 + timedelta(hours=2)
    )

    report = report_service.student_concept_report(db_session, ana, course_setup["course"])

    assert (stat_of(report, "Loops").passed, stat_of(report, "Loops").total) == (2, 3)


def test_hidden_tests_are_anonymous_in_the_student_report(
    db_session, course_setup, make_submission
):
    ana = course_setup["ana"]
    make_submission(ana, course_setup["assignment"], [P, P, F])

    report = report_service.student_concept_report(db_session, ana, course_setup["course"])

    negative = stat_of(report, "Negative numbers")
    (test,) = negative.tests
    assert test.test_name == "Hidden test #1"
    assert test.is_hidden is True
    assert test.verdict.value == "wrong_answer"
    assert negative.level == "review"


def test_two_students_see_different_reports(db_session, course_setup, make_submission):
    ana, bogdan, course = course_setup["ana"], course_setup["bogdan"], course_setup["course"]
    make_submission(ana, course_setup["assignment"], [P, P, F])
    make_submission(bogdan, course_setup["assignment"], [P, P, P])

    ana_report = report_service.student_concept_report(db_session, ana, course)
    bogdan_report = report_service.student_concept_report(db_session, bogdan, course)

    assert stat_of(ana_report, "Negative numbers").level == "review"
    assert stat_of(bogdan_report, "Negative numbers").level == "mastered"


def test_drafts_and_other_courses_do_not_count(
    db_session, course_setup, make_submission, make_assignment, make_test_case, make_course
):
    ana, course = course_setup["ana"], course_setup["course"]
    draft = make_assignment(course, title="Draft", is_published=False)
    make_test_case(draft, concepts=list(course_setup["assignment"].test_cases[0].concepts))
    make_submission(ana, draft, [F])

    report = report_service.student_concept_report(db_session, ana, course)

    assert report.concepts == []
    assert report.tests_total == 0


def test_class_report_averages_students_and_skips_those_who_left(
    db_session, course_setup, make_submission, make_user
):
    ana, bogdan, course = course_setup["ana"], course_setup["bogdan"], course_setup["course"]
    gone = make_user(Role.student)
    db_session.add(Enrollment(user_id=gone.id, course_id=course.id))
    db_session.commit()
    make_submission(ana, course_setup["assignment"], [P, F, F])  # Loops 1/3, Negative 0/1
    make_submission(bogdan, course_setup["assignment"], [P, P, P])  # Loops 3/3, Negative 1/1
    make_submission(gone, course_setup["assignment"], [F, F, F])
    db_session.delete(db_session.get(Enrollment, (gone.id, course.id)))
    db_session.commit()
    db_session.refresh(course)

    report = report_service.class_concept_report(db_session, course)

    assert (report.students, report.students_with_data) == (2, 2)
    loops = next(c for c in report.concepts if c.concept == "Loops")
    assert loops.average_pass_rate == pytest.approx((1 / 3 + 1) / 2)
    assert (loops.students_in_review, loops.students_mastered) == (1, 1)
    negative = next(c for c in report.concepts if c.concept == "Negative numbers")
    assert negative.average_pass_rate == pytest.approx(0.5)
    assert negative.level == "progress"


def test_dashboard_and_profile_use_the_report(db_session, course_setup, make_submission):
    ana = course_setup["ana"]
    make_submission(ana, course_setup["assignment"], [P, F, F])  # Loops 1/3, Negative 0/1

    dashboard = dashboard_service.student_dashboard(db_session, ana)
    activity = dashboard_service.user_activity(db_session, ana)

    assert dashboard.stats.concepts_to_review == 2
    first = dashboard.concepts_to_review[0]
    assert (first.concept, first.passed, first.total) == ("Negative numbers", 0, 1)
    assert [v.value for v in dashboard.concepts_to_review[1].verdicts] == [
        "passed",
        "wrong_answer",
        "wrong_answer",
    ]
    assert activity.totals.concepts_mastered == 0


def test_mastered_concepts_are_counted_on_the_profile(db_session, course_setup, make_submission):
    bogdan = course_setup["bogdan"]
    make_submission(bogdan, course_setup["assignment"], [P, P, P])

    activity = dashboard_service.user_activity(db_session, bogdan)
    dashboard = dashboard_service.student_dashboard(db_session, bogdan)

    assert activity.totals.concepts_mastered == 2
    assert dashboard.concepts_to_review == []
