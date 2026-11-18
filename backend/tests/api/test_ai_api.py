import pytest
from pydantic import SecretStr

from app.ai.client import FakeLLMClient, get_llm_client
from app.core.config import get_settings
from app.models import Role
from app.runner.factory import get_runner
from tests.fakes import FakeRunner, ok

API = "/api/v1"
SOLUTION = "print(sum(int(d) for d in input() if d.isdigit()))"


def digit_sum(code, stdin, limits):
    return ok(f"{sum(int(c) for c in stdin if c.isdigit())}\n")


def scripted_answer():
    return {
        "reference_solution": SOLUTION,
        "tests": [
            {
                "name": "Simple",
                "input": "1234\n",
                "concepts": ["Loops"],
                "hidden": False,
                "weight": 2,
                "rationale": "a plain number",
            },
            {
                "name": "Negative",
                "input": "-9075\n",
                "concepts": [],
                "hidden": True,
                "weight": 3,
                "rationale": "the sign is ignored",
            },
        ],
    }


@pytest.fixture
def with_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "anthropic_api_key", SecretStr("test-key"))


@pytest.fixture
def setup(client, make_user, make_course, make_assignment, make_concept, make_test_case):
    teacher, student = make_user(Role.teacher), make_user(Role.student)
    course = make_course(teacher, students=[student])
    make_concept(course, "Loops")
    assignment = make_assignment(course, description="Print the sum of the digits of n.")
    make_test_case(assignment, name="Manual")
    llm = FakeLLMClient([scripted_answer()])
    client.app.dependency_overrides[get_llm_client] = lambda: llm
    client.app.dependency_overrides[get_runner] = lambda: FakeRunner(digit_sum)
    return teacher, student, course, assignment, llm


def test_config_says_whether_ai_is_available(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "anthropic_api_key", SecretStr(""))
    assert client.get(f"{API}/config").json() == {"ai_available": False}

    monkeypatch.setattr(get_settings(), "anthropic_api_key", SecretStr("key"))
    assert client.get(f"{API}/config").json() == {"ai_available": True}

    monkeypatch.setattr(get_settings(), "ai_enabled", False)
    assert client.get(f"{API}/config").json() == {"ai_available": False}


def test_generation_end_to_end_then_approve(client, auth, setup, with_key):
    teacher, student, _, assignment, llm = setup
    headers = auth(teacher)

    started = client.post(
        f"{API}/assignments/{assignment.id}/generate-tests", json={"count": 6}, headers=headers
    )
    assert started.status_code == 202
    job = client.get(f"{API}/generation-jobs/{started.json()['job_id']}", headers=headers).json()

    assert (job["status"], job["phase"]) == ("done", "done")
    assert (job["tests_requested"], job["tests_proposed"], job["tests_kept"]) == (6, 2, 2)
    assert job["reference_code"] == SOLUTION
    assert "Write 6 tests" in llm.calls[0][1]

    drafts = client.get(
        f"{API}/assignments/{assignment.id}/test-cases", params={"review": "draft"}, headers=headers
    ).json()
    assert [(t["name"], t["expected_output"], t["source"]) for t in drafts] == [
        ("Simple", "10\n", "ai"),
        ("Negative", "21\n", "ai"),
    ]
    assert drafts[0]["concepts"][0]["name"] == "Loops"
    assert drafts[0]["ai_rationale"] == "a plain number"

    # Students see neither the drafts nor the job.
    as_student = client.get(f"{API}/assignments/{assignment.id}/test-cases", headers=auth(student))
    assert [t["name"] for t in as_student.json()] == ["Manual"]
    assert (
        client.get(f"{API}/assignments/{assignment.id}", headers=auth(student)).json()["test_count"]
        == 1
    )
    assert (
        client.get(f"{API}/generation-jobs/{job['id']}", headers=auth(student)).status_code == 403
    )

    one = client.post(f"{API}/test-cases/{drafts[0]['id']}/approve", headers=headers)
    rest = client.post(f"{API}/assignments/{assignment.id}/tests/approve-all", headers=headers)

    assert one.json()["review_status"] == "approved"
    assert rest.json() == {"approved": 1}
    teacher_view = client.get(f"{API}/assignments/{assignment.id}", headers=headers).json()
    assert (teacher_view["test_count"], teacher_view["draft_test_count"]) == (3, 0)


def test_without_a_key_generation_answers_503(client, auth, setup, monkeypatch):
    teacher, _, _, assignment, llm = setup
    monkeypatch.setattr(get_settings(), "anthropic_api_key", SecretStr(""))

    response = client.post(
        f"{API}/assignments/{assignment.id}/generate-tests", headers=auth(teacher)
    )

    assert response.status_code == 503
    assert response.json()["code"] == "service_unavailable"
    assert llm.calls == []


def test_count_must_be_between_4_and_12(client, auth, setup, with_key):
    teacher, _, _, assignment, _ = setup

    for count in (3, 13):
        response = client.post(
            f"{API}/assignments/{assignment.id}/generate-tests",
            json={"count": count},
            headers=auth(teacher),
        )
        assert response.status_code == 422


def test_other_teachers_and_students_cannot_start_or_read_jobs(
    client, auth, setup, with_key, make_user
):
    teacher, student, _, assignment, _ = setup
    other = make_user(Role.teacher)
    url = f"{API}/assignments/{assignment.id}/generate-tests"

    assert client.post(url, headers=auth(student)).status_code == 403
    assert client.post(url, headers=auth(other)).status_code == 404
    job_id = client.post(url, headers=auth(teacher)).json()["job_id"]
    assert client.get(f"{API}/generation-jobs/{job_id}", headers=auth(other)).status_code == 404
    assert client.get(f"{API}/generation-jobs/999999", headers=auth(teacher)).status_code == 404


def test_the_api_key_never_appears_in_answers(client, auth, setup, monkeypatch):
    teacher, _, _, assignment, _ = setup
    monkeypatch.setattr(get_settings(), "anthropic_api_key", SecretStr("sk-ant-secret-value"))

    started = client.post(
        f"{API}/assignments/{assignment.id}/generate-tests", headers=auth(teacher)
    )
    job = client.get(f"{API}/generation-jobs/{started.json()['job_id']}", headers=auth(teacher))
    config = client.get(f"{API}/config")

    for response in (started, job, config):
        assert "sk-ant-secret-value" not in response.text


def test_reindex_returns_the_number_of_text_pages(client, auth, setup, make_material):
    teacher, _, course, _, _ = setup
    material = make_material(course, pages=2)

    response = client.post(f"{API}/materials/{material.id}/reindex", headers=auth(teacher))

    assert response.status_code == 200
    assert response.json()["text_pages"] == 0  # blank pages: nothing to search
