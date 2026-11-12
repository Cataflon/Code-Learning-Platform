import threading
import time

import pytest

from app.models import Role, Submission, SubmissionStatus, Verdict
from app.runner.base import Limits, RunResult
from app.services import submission_service
from app.services.submission_runner import (
    INTERRUPTED_MESSAGE,
    recover_interrupted_submissions,
    run_submission,
)
from tests.fakes import FakeRunner, ok


@pytest.fixture
def setup(make_user, make_course, make_assignment, make_test_case):
    student = make_user(Role.student)
    assignment = make_assignment(make_course(students=[student]))
    make_test_case(assignment, name="first", input_data="1\n", expected_output="1\n")
    make_test_case(assignment, name="second", input_data="2\n", expected_output="2\n")
    make_test_case(assignment, name="third", input_data="3\n", expected_output="3\n")
    return student, assignment


def one_slot() -> threading.BoundedSemaphore:
    return threading.BoundedSemaphore(1)


def test_run_submission_goes_queued_running_done_and_saves_results_in_order(
    db_session, background_session_factory, setup
):
    student, assignment = setup
    submission = submission_service.create_submission(db_session, student, assignment, "code")
    seen: list[tuple[SubmissionStatus, int]] = []

    def observing_runner(code: str, stdin: str, limits: Limits) -> RunResult:
        # What a polling client would see while this test is running.
        db_session.expire_all()
        current = db_session.get(Submission, submission.id)
        seen.append((current.status, len(current.results)))
        return ok(stdin)

    assert submission.status == SubmissionStatus.queued
    run_submission(
        submission.id, background_session_factory, FakeRunner(observing_runner), one_slot()
    )

    db_session.expire_all()
    finished = db_session.get(Submission, submission.id)
    # During the run the status was "running" and the results appeared one by one.
    assert seen == [
        (SubmissionStatus.running, 0),
        (SubmissionStatus.running, 1),
        (SubmissionStatus.running, 2),
    ]
    assert finished.status == SubmissionStatus.done
    assert finished.score == 100
    assert finished.started_at is not None and finished.finished_at is not None
    ordered = sorted(finished.results, key=lambda result: result.id)
    assert [result.test_case.name for result in ordered] == ["first", "second", "third"]
    assert all(result.verdict == Verdict.passed for result in ordered)


def test_runner_error_leads_to_error_status(db_session, background_session_factory, setup):
    student, assignment = setup
    submission = submission_service.create_submission(db_session, student, assignment, "code")

    run_submission(
        submission.id,
        background_session_factory,
        FakeRunner([ok("1"), RuntimeError("docker down")]),
        one_slot(),
    )

    db_session.expire_all()
    failed = db_session.get(Submission, submission.id)
    assert failed.status == SubmissionStatus.error
    assert failed.finished_at is not None


def test_a_submission_that_is_not_queued_is_not_run_again(
    db_session, background_session_factory, setup
):
    student, assignment = setup
    submission = submission_service.create_submission(db_session, student, assignment, "code")
    submission.status = SubmissionStatus.done
    db_session.commit()
    runner = FakeRunner([ok("1")])

    run_submission(submission.id, background_session_factory, runner, one_slot())
    run_submission(999_999, background_session_factory, runner, one_slot())  # unknown id

    assert runner.calls == []


def test_recovery_marks_queued_and_running_submissions_as_error(db_session, setup):
    student, assignment = setup
    queued = submission_service.create_submission(db_session, student, assignment, "a")
    running = submission_service.create_submission(db_session, student, assignment, "b")
    done = submission_service.create_submission(db_session, student, assignment, "c")
    running.status = SubmissionStatus.running
    done.status = SubmissionStatus.done
    db_session.commit()

    recovered = recover_interrupted_submissions(db_session)

    assert recovered == 2
    assert queued.status == SubmissionStatus.error
    assert running.status == SubmissionStatus.error
    assert running.error_message == INTERRUPTED_MESSAGE
    assert done.status == SubmissionStatus.done


def test_application_startup_runs_the_recovery(client, db_session, setup):
    """`client` has already started the app; a fresh start must recover stuck submissions."""
    from fastapi.testclient import TestClient

    student, assignment = setup
    stuck = submission_service.create_submission(db_session, student, assignment, "a")
    stuck.status = SubmissionStatus.running
    db_session.commit()

    with TestClient(client.app):  # entering the context runs the lifespan startup hook
        pass

    db_session.expire_all()
    assert db_session.get(Submission, stuck.id).status == SubmissionStatus.error


def test_semaphore_makes_the_second_run_wait_for_the_first():
    """With one slot and a slow runner, runs never overlap (no database needed here)."""
    slots = one_slot()
    events: list[str] = []
    lock = threading.Lock()

    def slow_job(name: str) -> None:
        with slots:
            with lock:
                events.append(f"start {name}")
            time.sleep(0.15)
            with lock:
                events.append(f"end {name}")

    threads = [threading.Thread(target=slow_job, args=(name,)) for name in ("a", "b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Whichever started first also finished before the other one started.
    assert events[0].startswith("start") and events[1].startswith("end")
    assert events[0].split()[1] == events[1].split()[1]
    assert events[2].startswith("start") and events[3].startswith("end")


def test_run_submission_holds_a_slot_while_it_evaluates(
    db_session, background_session_factory, setup
):
    student, assignment = setup
    submission = submission_service.create_submission(db_session, student, assignment, "code")
    slots = one_slot()
    free_during_run: list[bool] = []

    def checking_runner(code: str, stdin: str, limits: Limits) -> RunResult:
        acquired = slots.acquire(blocking=False)
        free_during_run.append(acquired)
        if acquired:
            slots.release()
        return ok(stdin)

    run_submission(submission.id, background_session_factory, FakeRunner(checking_runner), slots)

    assert free_during_run == [False, False, False]  # the slot was taken for the whole run
    assert slots.acquire(blocking=False) is True  # and released afterwards


def test_application_startup_removes_orphaned_sandbox_containers(client):
    from fastapi.testclient import TestClient

    from app.runner.factory import get_runner

    class RunnerWithLeftovers:
        cleaned = 0

        def remove_leftover_containers(self) -> int:
            self.cleaned += 1
            return 2

    runner = RunnerWithLeftovers()
    client.app.dependency_overrides[get_runner] = lambda: runner

    with TestClient(client.app):
        pass

    assert runner.cleaned == 1


def test_application_still_starts_when_docker_is_unreachable(client):
    from fastapi.testclient import TestClient

    from app.runner.factory import get_runner

    class BrokenRunner:
        def remove_leftover_containers(self) -> int:
            raise ConnectionError("docker daemon is not running")

    client.app.dependency_overrides[get_runner] = lambda: BrokenRunner()

    with TestClient(client.app) as restarted:
        assert restarted.get("/health").status_code == 200
