from datetime import UTC, datetime, timedelta

import pytest

from app.models import Role

API = "/api/v1"
P, F = True, False


@pytest.fixture
def school(make_user, make_course, make_assignment, make_test_case, make_submission):
    teacher = make_user(Role.teacher)
    students = [make_user(Role.student, full_name=f"Student {letter}") for letter in "ABCDE"]
    course = make_course(teacher, students=students)
    assignment = make_assignment(course)
    make_test_case(assignment, name="t1")
    make_test_case(assignment, name="t2", is_hidden=True)
    start = datetime.now(UTC) - timedelta(hours=6)
    for index, student in enumerate(students):
        make_submission(
            student, assignment, [P, index % 2 == 0], created_at=start + timedelta(hours=index)
        )
    return teacher, students, course, assignment


def test_student_dashboard_contains_only_own_data(client, auth, school):
    _, students, _, assignment = school

    response = client.get(f"{API}/me/dashboard", headers=auth(students[1]))

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "stats",
        "courses",
        "assignments",
        "recent_submissions",
        "concepts_to_review",
    }
    item = body["assignments"][0]
    assert item["id"] == assignment.id
    assert item["best_score"] == 50
    assert item["last_verdicts"] == ["passed", "wrong_answer"]
    assert len(body["recent_submissions"]) == 1  # not the other four students' submissions


def test_teacher_list_is_paginated_and_filtered(client, auth, school):
    teacher, _, _, assignment = school
    url = f"{API}/assignments/{assignment.id}/submissions"

    first = client.get(url, params={"page_size": 2}, headers=auth(teacher)).json()
    third = client.get(url, params={"page_size": 2, "page": 3}, headers=auth(teacher)).json()
    correct = client.get(url, params={"verdict": "correct"}, headers=auth(teacher)).json()
    searched = client.get(url, params={"q": "student c"}, headers=auth(teacher)).json()

    assert first["total"] == 5 and first["page"] == 1 and first["page_size"] == 2
    assert [item["student_name"] for item in first["items"]] == ["Student E", "Student D"]
    assert [item["student_name"] for item in third["items"]] == ["Student A"]
    assert first["counts"] == {"all": 5, "correct": 3, "partial": 2, "wrong": 0, "running": 0}
    assert correct["total"] == 3
    assert all(item["score"] == 100 for item in correct["items"])
    assert [item["student_name"] for item in searched["items"]] == ["Student C"]


def test_invalid_filter_and_page_values_return_422(client, auth, school):
    teacher, _, _, assignment = school
    url = f"{API}/assignments/{assignment.id}/submissions"

    assert client.get(url, params={"verdict": "nope"}, headers=auth(teacher)).status_code == 422
    assert client.get(url, params={"page": 0}, headers=auth(teacher)).status_code == 422
    assert client.get(url, params={"page_size": 1000}, headers=auth(teacher)).status_code == 422


def test_assignment_stats_shape(client, auth, school):
    teacher, _, _, assignment = school

    body = client.get(f"{API}/assignments/{assignment.id}/stats", headers=auth(teacher)).json()

    assert body["submission_count"] == 5
    assert body["submitted_count"] == 5 and body["enrolled_count"] == 5
    assert body["average_score"] == 80  # three at 100, two at 50
    assert [(t["name"], t["passed"], t["total"]) for t in body["tests"]] == [
        ("t1", 5, 5),
        ("t2", 3, 5),
    ]
    assert body["tests"][1]["is_hidden"] is True
    assert [bucket["count"] for bucket in body["score_distribution"]] == [0, 2, 0, 0, 3]


def test_teacher_assignment_list_has_submitted_count_and_buckets(client, auth, school):
    teacher, students, course, _ = school
    url = f"{API}/courses/{course.id}/assignments"

    as_teacher = client.get(url, headers=auth(teacher)).json()[0]
    as_student = client.get(url, headers=auth(students[0])).json()[0]

    assert as_teacher["submitted_count"] == 5
    assert as_teacher["enrolled_count"] == 5
    assert as_teacher["result_buckets"] == {"full": 3, "partial": 2, "none": 0}
    assert as_student["submitted_count"] is None
    assert as_student["result_buckets"] is None


def test_course_stats_and_activity(client, auth, school):
    teacher, students, course, _ = school

    stats = client.get(f"{API}/courses/{course.id}/stats", headers=auth(teacher)).json()
    activity = client.get(
        f"{API}/users/me/activity", params={"weeks": 2}, headers=auth(students[0])
    ).json()

    assert stats["students"] == 5
    assert stats["average_score"] == 80
    assert activity["weeks"] == 2
    assert activity["totals"] == {"submissions": 1, "solved": 1, "concepts_mastered": 0}
    assert sum(day["count"] for day in activity["days"]) == 1


def test_activity_weeks_out_of_range_returns_422(client, auth, school):
    _, students, _, _ = school

    response = client.get(
        f"{API}/users/me/activity", params={"weeks": 500}, headers=auth(students[0])
    )

    assert response.status_code == 422
