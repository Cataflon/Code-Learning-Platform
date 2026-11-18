import pytest

from app.models import Role

API = "/api/v1"
P, F = True, False


@pytest.fixture
def setup(make_user, make_course, make_assignment, make_test_case, make_concept, make_submission):
    teacher = make_user(Role.teacher)
    ana, bogdan = make_user(Role.student), make_user(Role.student)
    course = make_course(teacher, students=[ana, bogdan])
    loops = make_concept(course, "Loops")
    assignment = make_assignment(course)
    make_test_case(assignment, name="Visible", concepts=[loops])
    make_test_case(
        assignment, name="Secret name", is_hidden=True, input_data="-9075\n", concepts=[loops]
    )
    make_submission(ana, assignment, [P, F])
    make_submission(bogdan, assignment, [P, P])
    return teacher, ana, bogdan, course


def test_student_gets_only_their_own_report(client, auth, setup):
    _, ana, _, course = setup

    response = client.get(f"{API}/courses/{course.id}/reports/concepts/me", headers=auth(ana))

    assert response.status_code == 200
    body = response.json()
    assert body["course_title"] == course.title
    assert (body["tests_passed"], body["tests_total"]) == (1, 2)
    assert body["verdicts"] == ["passed", "wrong_answer"]
    assert body["thresholds"] == {"review_below": 0.5, "mastered_from": 0.8}
    (loops,) = body["concepts"]
    assert loops["level"] == "progress"
    assert [t["test_name"] for t in loops["tests"]] == ["Visible", "Hidden test #1"]
    assert "Secret name" not in response.text
    assert "-9075" not in response.text


def test_teacher_gets_the_class_report(client, auth, setup):
    teacher, _, _, course = setup

    response = client.get(f"{API}/courses/{course.id}/reports/concepts", headers=auth(teacher))

    assert response.status_code == 200
    body = response.json()
    assert (body["students"], body["students_with_data"]) == (2, 2)
    (loops,) = body["concepts"]
    assert loops["average_pass_rate"] == pytest.approx(0.75)
    assert (loops["students_in_review"], loops["students_mastered"]) == (0, 1)


def test_student_without_submissions_gets_an_empty_report(
    client, auth, setup, make_user, db_session
):
    _, _, _, course = setup
    newcomer = make_user(Role.student)
    from app.models import Enrollment

    db_session.add(Enrollment(user_id=newcomer.id, course_id=course.id))
    db_session.commit()

    body = client.get(
        f"{API}/courses/{course.id}/reports/concepts/me", headers=auth(newcomer)
    ).json()

    assert body["concepts"] == []
    assert body["tests_total"] == 0


def test_dashboard_lists_concepts_to_review(
    client,
    auth,
    make_user,
    make_course,
    make_assignment,
    make_test_case,
    make_concept,
    make_submission,
):
    student = make_user(Role.student)
    course = make_course(students=[student])
    edge = make_concept(course, "Edge cases")
    assignment = make_assignment(course)
    for _ in range(3):
        make_test_case(assignment, concepts=[edge])
    make_submission(student, assignment, [P, F, F])

    body = client.get(f"{API}/me/dashboard", headers=auth(student)).json()

    assert body["stats"]["concepts_to_review"] == 1
    assert body["concepts_to_review"] == [
        {
            "concept": "Edge cases",
            "passed": 1,
            "total": 3,
            "verdicts": ["passed", "wrong_answer", "wrong_answer"],
        }
    ]
