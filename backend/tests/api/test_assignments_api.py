API = "/api/v1"


def test_teacher_creates_assignment_with_defaults(client, auth, teacher, make_course):
    course = make_course(teacher)

    response = client.post(
        f"{API}/courses/{course.id}/assignments", json={"title": "Digit sum"}, headers=auth(teacher)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["time_limit_ms"] == 2000
    assert body["memory_limit_mb"] == 128
    assert body["max_submissions"] == 10
    assert body["is_published"] is False
    assert body["status"] == "draft"
    assert body["language"] == "python"


def test_assignment_limits_are_validated(client, auth, teacher, make_course):
    course = make_course(teacher)

    response = client.post(
        f"{API}/courses/{course.id}/assignments",
        json={"title": "x", "time_limit_ms": 999999},
        headers=auth(teacher),
    )

    assert response.status_code == 422


def test_students_only_see_published_assignments(
    client, auth, teacher, student, make_course, make_assignment
):
    course = make_course(teacher, students=[student])
    published = make_assignment(course, title="Open one")
    make_assignment(course, title="Draft one", is_published=False)
    url = f"{API}/courses/{course.id}/assignments"

    as_student = client.get(url, headers=auth(student)).json()
    as_teacher = client.get(url, headers=auth(teacher)).json()

    assert [item["id"] for item in as_student] == [published.id]
    assert len(as_teacher) == 2


def test_publish_update_and_delete_assignment(client, auth, teacher, make_course, make_assignment):
    assignment = make_assignment(make_course(teacher), is_published=False)
    url = f"{API}/assignments/{assignment.id}"

    published = client.patch(url, json={"is_published": True}, headers=auth(teacher))
    deleted = client.delete(url, headers=auth(teacher))

    assert published.json()["status"] == "open"
    assert deleted.status_code == 204
    assert client.get(url, headers=auth(teacher)).status_code == 404


def test_teacher_creates_test_case_with_concepts(
    client, auth, teacher, make_course, make_assignment, make_concept
):
    course = make_course(teacher)
    assignment = make_assignment(course)
    concept = make_concept(course, "Loops")

    response = client.post(
        f"{API}/assignments/{assignment.id}/test-cases",
        json={
            "name": "Simple case",
            "input_data": "1234\n",
            "expected_output": "10\n",
            "weight": 3,
            "concept_ids": [concept.id],
        },
        headers=auth(teacher),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["position"] == 0
    assert body["concepts"] == [{"id": concept.id, "name": "Loops"}]


def test_test_case_with_foreign_concept_returns_422(
    client, auth, teacher, make_course, make_assignment, make_concept
):
    assignment = make_assignment(make_course(teacher))
    foreign = make_concept(make_course(teacher), "Other")

    response = client.post(
        f"{API}/assignments/{assignment.id}/test-cases",
        json={"name": "t", "concept_ids": [foreign.id]},
        headers=auth(teacher),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_data"


def test_student_sees_only_public_tests_without_hint_or_weight(
    client, auth, teacher, student, make_course, make_assignment, make_test_case
):
    assignment = make_assignment(make_course(teacher, students=[student]))
    public = make_test_case(assignment, name="Public", hint="a hint")
    make_test_case(assignment, name="Secret", is_hidden=True, input_data="-9075\n")
    url = f"{API}/assignments/{assignment.id}/test-cases"

    as_student = client.get(url, headers=auth(student)).json()
    as_teacher = client.get(url, headers=auth(teacher)).json()

    assert [item["id"] for item in as_student] == [public.id]
    assert "hint" not in as_student[0]
    assert "weight" not in as_student[0]
    assert [item["name"] for item in as_teacher] == ["Public", "Secret"]
    assert as_teacher[1]["input_data"] == "-9075\n"


def test_update_and_delete_test_case(
    client, auth, teacher, make_course, make_assignment, make_test_case
):
    test_case = make_test_case(make_assignment(make_course(teacher)))
    url = f"{API}/test-cases/{test_case.id}"

    updated = client.patch(url, json={"is_hidden": True, "weight": 4}, headers=auth(teacher))
    deleted = client.delete(url, headers=auth(teacher))

    assert updated.json()["is_hidden"] is True
    assert updated.json()["weight"] == 4
    assert deleted.status_code == 204
    assert client.patch(url, json={"weight": 1}, headers=auth(teacher)).status_code == 404
