import pytest

from app.core.config import get_settings
from app.models import Role
from app.runner.factory import get_runner
from tests.fakes import FakeRunner, echo_runner

API = "/api/v1"


@pytest.fixture
def setup(client, make_user, make_course, make_assignment, make_test_case):
    client.app.dependency_overrides[get_runner] = echo_runner
    teacher, student = make_user(Role.teacher), make_user(Role.student)
    assignment = make_assignment(make_course(teacher, students=[student]))
    make_test_case(assignment, name="Simple case")  # 1234 -> 10
    make_test_case(
        assignment,
        name="Secret name",
        is_hidden=True,
        input_data="-9075\n",
        expected_output="99\n",  # the echo runner answers 21, so this one fails
        hint="Check the sign.",
    )
    return teacher, student, assignment


def test_post_answers_202_queued_and_get_returns_the_finished_result(client, auth, setup):
    _, student, assignment = setup

    response = client.post(
        f"{API}/assignments/{assignment.id}/submissions",
        json={"code": "print(1)"},
        headers=auth(student),
    )

    # The response is sent before any test runs: queued, no score, every verdict pending.
    assert response.status_code == 202
    queued = response.json()
    assert queued["status"] == "queued"
    assert queued["score"] is None
    assert queued["verdicts"] == [None, None]
    # TestClient runs the background task before returning, so polling now sees the end state.
    body = client.get(f"{API}/submissions/{queued['id']}", headers=auth(student)).json()
    assert body["status"] == "done"
    assert (body["score"], body["passed_count"], body["total_count"]) == (50, 1, 2)
    assert body["verdicts"] == ["passed", "wrong_answer"]
    assert body["attempt_number"] == 1
    assert [result["verdict"] for result in body["results"]] == ["passed", "wrong_answer"]


def test_hidden_test_content_is_missing_from_the_student_response(client, auth, setup):
    teacher, student, assignment = setup
    created = client.post(
        f"{API}/assignments/{assignment.id}/submissions",
        json={"code": "print(1)"},
        headers=auth(student),
    ).json()
    url = f"{API}/submissions/{created['id']}"

    as_student = client.get(url, headers=auth(student))
    as_teacher = client.get(url, headers=auth(teacher))

    hidden = as_student.json()["results"][1]
    assert hidden["name"] == "Hidden test #1"
    assert hidden["input_data"] is None
    assert hidden["expected_output"] is None
    assert hidden["actual_output"] is None
    assert hidden["hint"] == "Check the sign."
    assert "Secret name" not in as_student.text
    assert "-9075" not in as_student.text
    assert as_teacher.json()["results"][1]["name"] == "Secret name"
    assert as_teacher.json()["code"] == "print(1)"


def test_student_who_is_not_enrolled_gets_404(client, auth, setup, make_user):
    _, _, assignment = setup
    outsider = make_user(Role.student)

    response = client.post(
        f"{API}/assignments/{assignment.id}/submissions",
        json={"code": "print(1)"},
        headers=auth(outsider),
    )

    assert response.status_code == 404


def test_teacher_cannot_submit(client, auth, setup):
    teacher, _, assignment = setup

    response = client.post(
        f"{API}/assignments/{assignment.id}/submissions",
        json={"code": "print(1)"},
        headers=auth(teacher),
    )

    assert response.status_code == 403


def test_other_student_cannot_read_a_submission(client, auth, setup, make_user, db_session):
    _, student, assignment = setup
    classmate = make_user(Role.student)
    from app.models import Enrollment

    db_session.add(Enrollment(user_id=classmate.id, course_id=assignment.course_id))
    db_session.commit()
    created = client.post(
        f"{API}/assignments/{assignment.id}/submissions",
        json={"code": "print(1)"},
        headers=auth(student),
    ).json()

    response = client.get(f"{API}/submissions/{created['id']}", headers=auth(classmate))
    listed = client.get(f"{API}/assignments/{assignment.id}/submissions", headers=auth(classmate))

    assert response.status_code == 404
    assert listed.json() == []


def test_empty_and_oversized_code_are_rejected(client, auth, setup):
    _, student, assignment = setup
    url = f"{API}/assignments/{assignment.id}/submissions"

    empty = client.post(url, json={"code": ""}, headers=auth(student))
    huge = client.post(url, json={"code": "x" * (64 * 1024 + 1)}, headers=auth(student))

    assert empty.status_code == 422
    assert huge.status_code == 422


def test_assignment_shows_submissions_left_to_the_student(client, auth, setup):
    teacher, student, assignment = setup
    url = f"{API}/assignments/{assignment.id}"
    client.post(f"{url}/submissions", json={"code": "print(1)"}, headers=auth(student))

    as_student = client.get(url, headers=auth(student)).json()
    as_teacher = client.get(url, headers=auth(teacher)).json()

    assert as_student["submissions_left"] == 9
    assert as_teacher["submissions_left"] is None


def test_list_returns_own_attempts_newest_first(client, auth, setup):
    _, student, assignment = setup
    url = f"{API}/assignments/{assignment.id}/submissions"
    for _ in range(2):
        client.post(url, json={"code": "print(1)"}, headers=auth(student))

    listed = client.get(url, headers=auth(student)).json()

    assert [item["attempt_number"] for item in listed] == [2, 1]
    assert "code" not in listed[0]
    assert listed[0]["verdicts"] == ["passed", "wrong_answer"]


def test_second_submission_inside_the_minimum_interval_gets_429(client, auth, setup, monkeypatch):
    _, student, assignment = setup
    monkeypatch.setattr(get_settings(), "min_submission_interval_s", 5)
    url = f"{API}/assignments/{assignment.id}/submissions"

    first = client.post(url, json={"code": "print(1)"}, headers=auth(student))
    second = client.post(url, json={"code": "print(1)"}, headers=auth(student))

    assert first.status_code == 202
    assert second.status_code == 429
    assert second.json()["code"] == "too_many_requests"
    assert int(second.headers["Retry-After"]) >= 1


def test_runner_crash_is_reported_as_error_status(client, auth, setup):
    _, student, assignment = setup
    client.app.dependency_overrides[get_runner] = lambda: FakeRunner([RuntimeError("docker down")])

    created = client.post(
        f"{API}/assignments/{assignment.id}/submissions",
        json={"code": "print(1)"},
        headers=auth(student),
    ).json()
    body = client.get(f"{API}/submissions/{created['id']}", headers=auth(student)).json()

    assert body["status"] == "error"
    assert "could not be evaluated" in body["error_message"]
    assert body["score"] is None
