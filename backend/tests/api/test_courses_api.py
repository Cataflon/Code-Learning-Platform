from app.models import Role

API = "/api/v1"


def test_teacher_creates_and_lists_course(client, auth, teacher):
    response = client.post(
        f"{API}/courses", json={"title": "Algorithms", "color": "blue"}, headers=auth(teacher)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Algorithms"
    assert body["color"] == "blue"
    assert body["teacher_name"] == teacher.full_name
    assert len(body["join_code"]) == 8
    listed = client.get(f"{API}/courses", headers=auth(teacher)).json()
    assert [course["id"] for course in listed] == [body["id"]]


def test_create_course_with_invalid_data_returns_422(client, auth, teacher):
    response = client.post(f"{API}/courses", json={"title": "   "}, headers=auth(teacher))

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert "detail" in response.json()


def test_get_unknown_course_returns_404_in_uniform_format(client, auth, teacher):
    response = client.get(f"{API}/courses/999999", headers=auth(teacher))

    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found", "code": "not_found"}


def test_update_and_delete_course(client, auth, teacher, make_course):
    course = make_course(teacher)

    updated = client.patch(
        f"{API}/courses/{course.id}",
        json={"title": "Renamed", "regenerate_join_code": True},
        headers=auth(teacher),
    )
    deleted = client.delete(f"{API}/courses/{course.id}", headers=auth(teacher))

    assert updated.status_code == 200
    assert updated.json()["title"] == "Renamed"
    assert deleted.status_code == 204
    assert client.get(f"{API}/courses/{course.id}", headers=auth(teacher)).status_code == 404


def test_student_joins_course_and_does_not_see_join_code(client, auth, student, make_course):
    course = make_course()

    response = client.post(
        f"{API}/courses/join", json={"join_code": course.join_code}, headers=auth(student)
    )

    assert response.status_code == 200
    assert response.json()["join_code"] is None
    listed = client.get(f"{API}/courses", headers=auth(student)).json()
    assert [item["id"] for item in listed] == [course.id]


def test_joining_twice_returns_409(client, auth, student, make_course):
    course = make_course(students=[student])

    response = client.post(
        f"{API}/courses/join", json={"join_code": course.join_code}, headers=auth(student)
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_list_students_returns_enrolled_students(client, auth, teacher, make_course, make_user):
    students = [make_user(Role.student, full_name=name) for name in ("Zoe", "Ana")]
    course = make_course(teacher, students=students)

    response = client.get(f"{API}/courses/{course.id}/students", headers=auth(teacher))

    assert response.status_code == 200
    assert [item["full_name"] for item in response.json()] == ["Ana", "Zoe"]
    assert "password_hash" not in response.json()[0]


def test_concepts_create_list_and_conflict(client, auth, teacher, make_course):
    course = make_course(teacher)
    url = f"{API}/courses/{course.id}/concepts"

    created = client.post(url, json={"name": "Loops"}, headers=auth(teacher))
    duplicate = client.post(url, json={"name": "Loops"}, headers=auth(teacher))
    listed = client.get(url, headers=auth(teacher))

    assert created.status_code == 201
    assert duplicate.status_code == 409
    assert [concept["name"] for concept in listed.json()] == ["Loops"]
