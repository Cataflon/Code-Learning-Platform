from datetime import UTC, datetime, timedelta

import pytest

from app.core.errors import ConflictError, InvalidDataError
from app.models import Role, SubmissionStatus, Verdict
from app.services import submission_service
from tests.fakes import FakeRunner, crash, ok, out_of_memory, timeout


@pytest.fixture
def setup(make_user, make_course, make_assignment, make_test_case, make_concept):
    teacher, student = make_user(Role.teacher), make_user(Role.student)
    course = make_course(teacher, students=[student])
    assignment = make_assignment(course)
    loops = make_concept(course, "Loops")
    make_test_case(assignment, name="Simple case", weight=3, concepts=[loops])
    make_test_case(assignment, name="Zero", weight=3, input_data="0\n", expected_output="0\n")
    make_test_case(
        assignment,
        name="Negative secret",
        weight=4,
        is_hidden=True,
        input_data="-9075\n",
        expected_output="21\n",
        hint="Check the sign.",
    )
    return teacher, student, assignment


def submit(db, student, assignment, script):
    submission = submission_service.create_submission(db, student, assignment, "print(1)")
    runner = FakeRunner(script)
    submission_service.evaluate_submission(db, submission, runner)
    return submission, runner


def test_all_tests_passed_gives_100(db_session, setup):
    _, student, assignment = setup

    submission, runner = submit(db_session, student, assignment, [ok("10"), ok("0"), ok("21")])

    assert submission.status == SubmissionStatus.done
    assert (submission.score, submission.passed_count, submission.total_count) == (100, 3, 3)
    assert submission.started_at is not None and submission.finished_at is not None
    assert [call[1] for call in runner.calls] == ["1234\n", "0\n", "-9075\n"]  # test order
    assert runner.calls[0][2].time_limit_ms == assignment.time_limit_ms


def test_every_verdict_is_stored_and_score_follows_weights(db_session, setup):
    _, student, assignment = setup
    stderr = 'Traceback\n  File "main.py", line 4, in <module>\nIndexError: list index out of range'

    submission, _ = submit(db_session, student, assignment, [ok("10"), crash(stderr), timeout()])

    verdicts = [result.verdict for result in sorted(submission.results, key=lambda r: r.id)]
    assert verdicts == [Verdict.passed, Verdict.runtime_error, Verdict.time_limit]
    assert submission.score == 30  # only the first test (weight 3 of 10) passed
    assert submission.error_excerpt == "IndexError, line 4"


def test_wrong_answer_and_memory_limit(db_session, setup):
    _, student, assignment = setup

    submission, _ = submit(db_session, student, assignment, [ok("999"), out_of_memory(), ok("21")])

    verdicts = [result.verdict for result in sorted(submission.results, key=lambda r: r.id)]
    assert verdicts == [Verdict.wrong_answer, Verdict.memory_limit, Verdict.passed]
    assert submission.score == 40


def test_runner_failure_ends_in_error_not_in_a_stuck_submission(db_session, setup):
    _, student, assignment = setup

    submission, _ = submit(db_session, student, assignment, [ok("10"), RuntimeError("docker down")])

    assert submission.status == SubmissionStatus.error
    assert "docker down" in submission.error_message
    assert submission.score is None
    assert submission.finished_at is not None


def test_hidden_tests_are_masked_for_students_but_not_for_teachers(db_session, setup):
    teacher, student, assignment = setup
    submission, _ = submit(db_session, student, assignment, [ok("10"), ok("0"), ok("wrong")])

    as_student = submission_service.get_visible_results(submission, student)
    as_teacher = submission_service.get_visible_results(submission, teacher)

    hidden = as_student[2]
    assert hidden.name == "Hidden test #1"
    assert hidden.is_hidden is True
    assert hidden.verdict == Verdict.wrong_answer
    assert hidden.input_data is None and hidden.expected_output is None
    assert hidden.actual_output is None and hidden.stderr is None
    assert hidden.hint == "Check the sign."  # failed, so the hint is shown
    assert as_student[0].input_data == "1234\n"
    assert as_student[0].concepts == ["Loops"]
    assert as_teacher[2].name == "Negative secret"
    assert as_teacher[2].input_data == "-9075\n"


def test_hint_is_not_shown_when_the_test_passed(db_session, setup):
    _, student, assignment = setup
    submission, _ = submit(db_session, student, assignment, [ok("10"), ok("0"), ok("21")])

    results = submission_service.get_visible_results(submission, student)

    assert results[2].hint is None


def test_summary_lists_verdicts_in_test_order_with_attempt_numbers(db_session, setup):
    _, student, assignment = setup
    submit(db_session, student, assignment, [ok("x"), ok("0"), ok("21")])
    submit(db_session, student, assignment, [ok("10"), ok("0"), ok("21")])

    submissions = submission_service.list_submissions(db_session, assignment, student)
    summaries = submission_service.to_summaries(db_session, submissions)

    assert [summary.attempt_number for summary in summaries] == [2, 1]  # newest first
    assert summaries[1].verdicts == [Verdict.wrong_answer, Verdict.passed, Verdict.passed]
    assert summaries[0].score == 100


def test_students_only_list_their_own_submissions(db_session, setup, make_user):
    teacher, student, assignment = setup
    other = make_user(Role.student)
    submit(db_session, student, assignment, [ok("10"), ok("0"), ok("21")])
    submit(db_session, other, assignment, [ok("10"), ok("0"), ok("21")])

    assert len(submission_service.list_submissions(db_session, assignment, student)) == 1
    assert len(submission_service.list_submissions(db_session, assignment, teacher)) == 2


def test_no_attempts_left_raises_conflict(db_session, setup):
    _, student, assignment = setup
    assignment.max_submissions = 1
    submit(db_session, student, assignment, [ok("10"), ok("0"), ok("21")])

    assert submission_service.submissions_left(db_session, student, assignment) == 0
    with pytest.raises(ConflictError):
        submission_service.create_submission(db_session, student, assignment, "print(1)")


def test_closed_assignment_and_assignment_without_tests_are_rejected(
    db_session, setup, make_assignment
):
    _, student, assignment = setup
    empty = make_assignment(assignment.course, title="Empty")
    assignment.due_at = datetime.now(UTC) - timedelta(hours=1)

    with pytest.raises(ConflictError):
        submission_service.create_submission(db_session, student, assignment, "print(1)")
    with pytest.raises(InvalidDataError):
        submission_service.create_submission(db_session, student, empty, "print(1)")
