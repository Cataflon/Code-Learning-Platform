"""Step 10: whole flows through the API, rate limits, input limits and the request id."""

from app.core.config import get_settings
from app.core.rate_limit import FixedWindowLimiter
from app.runner.factory import get_runner
from tests.fakes import echo_runner
from tests.files import pdf_bytes

API = "/api/v1"
PASSWORD = "parola123"


def register(client, email, name, role="student", invite_code=None):
    body = {"email": email, "full_name": name, "password": PASSWORD, "role": role}
    if invite_code:
        body["invite_code"] = invite_code
    response = client.post(f"{API}/auth/register", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def sign_in(client, email):
    response = client.post(f"{API}/auth/login", data={"username": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def teacher_with_assignment(client):
    """A teacher registers with an invite code and publishes a digit-sum assignment."""
    register(
        client, "prof@example.com", "Prof Ionescu", "teacher", get_settings().teacher_invite_code
    )
    teacher = sign_in(client, "prof@example.com")
    course = client.post(f"{API}/courses", json={"title": "Python"}, headers=teacher).json()
    loops = client.post(
        f"{API}/courses/{course['id']}/concepts", json={"name": "Loops"}, headers=teacher
    ).json()
    signs = client.post(
        f"{API}/courses/{course['id']}/concepts", json={"name": "Negative numbers"}, headers=teacher
    ).json()
    assignment = client.post(
        f"{API}/courses/{course['id']}/assignments",
        json={"title": "Digit sum", "description": "Print the sum of the digits."},
        headers=teacher,
    ).json()
    tests = [
        ("Simple", "1234\n", "10\n", False, loops["id"]),
        ("Negative", "-56\n", "-11\n", True, signs["id"]),  # the echo runner prints 11
    ]
    created = []
    for name, stdin, expected, hidden, concept in tests:
        created.append(
            client.post(
                f"{API}/assignments/{assignment['id']}/test-cases",
                json={
                    "name": name,
                    "input_data": stdin,
                    "expected_output": expected,
                    "is_hidden": hidden,
                    "concept_ids": [concept],
                },
                headers=teacher,
            ).json()
        )
    published = client.patch(
        f"{API}/assignments/{assignment['id']}", json={"is_published": True}, headers=teacher
    )
    assert published.status_code == 200
    return teacher, course, assignment, created


def test_the_whole_flow_from_registration_to_the_concept_report(client):
    client.app.dependency_overrides[get_runner] = echo_runner
    teacher, course, assignment, _ = teacher_with_assignment(client)

    register(client, "ana@example.com", "Ana Pop")
    student = sign_in(client, "ana@example.com")
    joined = client.post(
        f"{API}/courses/join", json={"join_code": course["join_code"]}, headers=student
    )
    assert joined.status_code == 200

    queued = client.post(
        f"{API}/assignments/{assignment['id']}/submissions",
        json={"code": "print(sum(map(int, input())))"},
        headers=student,
    )
    assert queued.status_code == 202
    # TestClient runs the background task before returning, so one poll sees the end.
    result = client.get(f"{API}/submissions/{queued.json()['id']}", headers=student).json()
    assert result["status"] == "done"
    assert (result["passed_count"], result["total_count"], result["score"]) == (1, 2, 50)

    report = client.get(f"{API}/courses/{course['id']}/reports/concepts/me", headers=student)
    levels = {row["concept"]: row["level"] for row in report.json()["concepts"]}
    assert levels == {"Negative numbers": "review", "Loops": "mastered"}

    class_report = client.get(f"{API}/courses/{course['id']}/reports/concepts", headers=teacher)
    assert class_report.status_code == 200


def test_the_materials_flow_ends_with_the_recommended_pages(client, file_store):
    client.app.dependency_overrides[get_runner] = echo_runner
    teacher, course, assignment, tests = teacher_with_assignment(client)
    uploaded = client.post(
        f"{API}/courses/{course['id']}/materials",
        files={"file": ("lecture.pdf", pdf_bytes(20), "application/pdf")},
        data={"title": "Lecture 4", "category": "lecture"},
        headers=teacher,
    )
    assert uploaded.status_code == 201
    material = uploaded.json()
    negative = next(test for test in tests if test["name"] == "Negative")
    linked = client.put(
        f"{API}/test-cases/{negative['id']}/materials",
        json=[{"material_id": material["id"], "pages": "12-15"}],
        headers=teacher,
    )
    assert linked.status_code == 200

    register(client, "ana@example.com", "Ana Pop")
    student = sign_in(client, "ana@example.com")
    client.post(f"{API}/courses/join", json={"join_code": course["join_code"]}, headers=student)
    submission = client.post(
        f"{API}/assignments/{assignment['id']}/submissions",
        json={"code": "print(1)"},
        headers=student,
    ).json()

    recommendations = client.get(
        f"{API}/submissions/{submission['id']}/recommendations", headers=student
    ).json()
    assert [test["name"] for test in recommendations["failed_tests"]] == ["Hidden test #1"]
    (recommended,) = recommendations["materials"]
    assert (recommended["title"], recommended["pages"], recommended["first_page"]) == (
        "Lecture 4",
        "12-15",
        12,
    )


def test_the_eleventh_sign_in_in_a_minute_gets_429(client, make_user):
    from app.models import Role

    make_user(Role.student, password=PASSWORD, email="s@example.com")
    for _ in range(10):
        wrong = client.post(
            f"{API}/auth/login", data={"username": "s@example.com", "password": "x"}
        )
        assert wrong.status_code == 401

    blocked = client.post(
        f"{API}/auth/login", data={"username": "s@example.com", "password": PASSWORD}
    )

    assert blocked.status_code == 429
    assert blocked.json()["code"] == "too_many_requests"
    assert 1 <= int(blocked.headers["Retry-After"]) <= 60


def test_a_fixed_window_opens_again_after_the_window():
    now = [0.0]
    limiter = FixedWindowLimiter(limit=2, window_s=60, clock=lambda: now[0])

    assert limiter.hit("ip") is None and limiter.hit("ip") is None
    assert limiter.hit("ip") == 60
    assert limiter.hit("other ip") is None  # each key has its own counter
    now[0] = 59.5
    assert limiter.hit("ip") == 0.5
    now[0] = 60.0
    assert limiter.hit("ip") is None


def test_submissions_are_limited_per_student(client, auth, make_user, make_course, monkeypatch):
    from app.models import Role

    monkeypatch.setattr(get_settings(), "rate_limit_submissions_per_minute", 2)
    client.app.dependency_overrides[get_runner] = echo_runner
    _, course, assignment, _ = teacher_with_assignment(client)
    student = make_user(Role.student)
    client.post(
        f"{API}/courses/join", json={"join_code": course["join_code"]}, headers=auth(student)
    )
    url = f"{API}/assignments/{assignment['id']}/submissions"

    statuses = [
        client.post(url, json={"code": "print(1)"}, headers=auth(student)).status_code
        for _ in range(3)
    ]

    assert statuses == [202, 202, 429]


def test_code_over_64_kb_is_refused_with_422(client, auth, make_user, make_course, make_assignment):
    from app.models import Role

    student = make_user(Role.student)
    assignment = make_assignment(make_course(make_user(Role.teacher), students=[student]))

    response = client.post(
        f"{API}/assignments/{assignment.id}/submissions",
        json={"code": "x" * (64 * 1024 + 1)},
        headers=auth(student),
    )

    assert response.status_code == 422


def test_every_answer_carries_a_request_id(client):
    fresh = client.get("/health")
    echoed = client.get("/health", headers={"X-Request-ID": "trace-123"})
    unsafe = client.get("/health", headers={"X-Request-ID": "bad id\nwith newline"})

    assert len(fresh.headers["X-Request-ID"]) == 32
    assert echoed.headers["X-Request-ID"] == "trace-123"
    assert unsafe.headers["X-Request-ID"] != "bad id\nwith newline"
    assert client.get(f"{API}/nope").headers["X-Request-ID"]  # errors too


def test_log_lines_carry_the_request_id(client, caplog):
    import logging

    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/health", headers={"X-Request-ID": "trace-456"})

    (line,) = [record for record in caplog.records if record.name == "app.access"]
    assert "GET /health -> 200" in line.getMessage()
