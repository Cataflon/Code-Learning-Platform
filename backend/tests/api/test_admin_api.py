"""The technical admin (decision D30): accounts, invite codes and the rules that protect them."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models import Enrollment, InviteCode, Role, Submission

API = "/api/v1"
TEACHER = {
    "email": "new.teacher@example.com",
    "full_name": "New Teacher",
    "password": "parola123",
    "role": "teacher",
}


@pytest.fixture
def admin(make_user):
    return make_user(Role.admin, full_name="Ada Admin")


def register(client, code, email="new.teacher@example.com"):
    return client.post(
        f"{API}/auth/register", json={**TEACHER, "email": email, "invite_code": code}
    )


def test_an_invite_code_lets_one_teacher_register_then_is_used(client, auth, admin):
    created = client.post(
        f"{API}/admin/invite-codes", json={"note": "Prof. Popescu"}, headers=auth(admin)
    )
    code = created.json()["code"]

    assert created.status_code == 201
    assert code.startswith("TEACH-") and len(code) == 15
    assert created.json()["status"] == "active"
    assert created.json()["created_by_name"] == "Ada Admin"

    first = register(client, code.lower())  # case does not matter
    second = register(client, code, email="another@example.com")

    assert first.status_code == 201 and first.json()["role"] == "teacher"
    assert second.status_code == 403
    assert "expired or was already used" in second.json()["detail"]
    listed = client.get(f"{API}/admin/invite-codes", headers=auth(admin)).json()
    assert listed[0]["status"] == "used"
    assert listed[0]["used_by"] == ["New Teacher"]
    users = client.get(f"{API}/admin/users", params={"role": "teacher"}, headers=auth(admin))
    assert users.json()["items"][0]["invite_code"] == code


def test_expired_and_revoked_codes_do_not_work(client, auth, admin, db_session):
    expired = InviteCode(
        code="TEACH-OLD1-OLD1",
        note="",
        max_uses=5,
        uses=0,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    db_session.add(expired)
    db_session.commit()
    revoked = client.post(f"{API}/admin/invite-codes", json={}, headers=auth(admin)).json()
    after = client.post(
        f"{API}/admin/invite-codes/{revoked['id']}/revoke", headers=auth(admin)
    ).json()

    assert after["status"] == "revoked"
    assert register(client, "TEACH-OLD1-OLD1").status_code == 403
    assert register(client, revoked["code"]).status_code == 403


def test_a_code_with_several_uses_and_no_expiry(client, auth, admin):
    code = client.post(
        f"{API}/admin/invite-codes",
        json={"max_uses": 2, "expires_in_days": None},
        headers=auth(admin),
    ).json()

    assert code["expires_at"] is None
    assert register(client, code["code"], email="a@example.com").status_code == 201
    assert register(client, code["code"], email="b@example.com").status_code == 201
    assert register(client, code["code"], email="c@example.com").status_code == 403


def test_nobody_registers_as_admin(client):
    response = client.post(
        f"{API}/auth/register", json={**TEACHER, "role": "admin", "invite_code": "PROF-2026"}
    )
    assert response.status_code == 403


def test_a_disabled_account_cannot_sign_in_and_its_token_stops_working(
    client, auth, admin, make_user
):
    student = make_user(Role.student, password="parola123", email="s@example.com")
    token_headers = auth(student)

    disabled = client.patch(
        f"{API}/admin/users/{student.id}", json={"is_active": False}, headers=auth(admin)
    )
    login = client.post(
        f"{API}/auth/login", data={"username": "s@example.com", "password": "parola123"}
    )

    assert disabled.json()["is_active"] is False
    assert login.status_code == 403
    assert "disabled" in login.json()["detail"]
    assert client.get(f"{API}/users/me", headers=token_headers).status_code == 401

    client.patch(f"{API}/admin/users/{student.id}", json={"is_active": True}, headers=auth(admin))
    assert client.get(f"{API}/users/me", headers=token_headers).status_code == 200


def test_reset_password_gives_a_temporary_password_once(client, auth, admin, make_user):
    student = make_user(Role.student, password="parola123", email="s@example.com")

    reset = client.post(f"{API}/admin/users/{student.id}/reset-password", headers=auth(admin))
    password = reset.json()["temporary_password"]

    assert len(password) == 14
    old = client.post(
        f"{API}/auth/login", data={"username": "s@example.com", "password": "parola123"}
    )
    new = client.post(f"{API}/auth/login", data={"username": "s@example.com", "password": password})
    assert (old.status_code, new.status_code) == (401, 200)


def test_rules_that_keep_an_admin_in_charge(client, auth, admin, make_user, make_course):
    headers = auth(admin)

    myself = client.patch(
        f"{API}/admin/users/{admin.id}", json={"is_active": False}, headers=headers
    )
    demote = client.patch(
        f"{API}/admin/users/{admin.id}", json={"role": "teacher"}, headers=headers
    )
    own_reset = client.post(f"{API}/admin/users/{admin.id}/reset-password", headers=headers)
    assert (myself.status_code, demote.status_code, own_reset.status_code) == (422, 422, 422)

    other = make_user(Role.admin)
    # Two admins: one may demote the other, but then the last one is protected.
    assert (
        client.patch(
            f"{API}/admin/users/{other.id}", json={"role": "teacher"}, headers=headers
        ).status_code
        == 200
    )

    teacher = make_user(Role.teacher)
    make_course(teacher)
    to_student = client.patch(
        f"{API}/admin/users/{teacher.id}", json={"role": "student"}, headers=headers
    )
    assert to_student.status_code == 409
    assert "owns 1 course" in to_student.json()["detail"]
    free_teacher = make_user(Role.teacher)  # owns no course, so the role may change
    promoted = client.patch(
        f"{API}/admin/users/{free_teacher.id}", json={"role": "admin"}, headers=headers
    )
    assert promoted.json()["role"] == "admin"


def test_users_list_searches_filters_and_counts(
    client, auth, admin, make_user, make_course, make_assignment, db_session
):
    teacher = make_user(Role.teacher, full_name="Maria Ionescu", email="maria@example.com")
    student = make_user(Role.student, full_name="Andrei Pop", email="andrei@example.com")
    make_user(Role.student, full_name="Elena Matei", email="elena@example.com", is_active=False)
    course = make_course(teacher, students=[student])
    assignment = make_assignment(course)
    db_session.add(Submission(assignment_id=assignment.id, student_id=student.id, code="print(1)"))
    db_session.commit()
    headers = auth(admin)

    found = client.get(f"{API}/admin/users", params={"q": "andrei"}, headers=headers).json()
    disabled = client.get(f"{API}/admin/users", params={"active": False}, headers=headers).json()
    teachers = client.get(f"{API}/admin/users", params={"role": "teacher"}, headers=headers).json()
    stats = client.get(f"{API}/admin/stats", headers=headers).json()

    assert found["total"] == 1
    andrei = found["items"][0]
    assert (andrei["courses_enrolled"], andrei["submissions"]) == (1, 1)
    assert [user["full_name"] for user in disabled["items"]] == ["Elena Matei"]
    assert teachers["items"][0]["courses_taught"] == 1
    assert stats["students"] == 2 and stats["teachers"] == 1 and stats["admins"] == 1
    assert (stats["disabled"], stats["courses"], stats["submissions"]) == (1, 1, 1)


def test_a_teacher_removes_a_student_who_keeps_their_submissions(
    client, auth, make_user, make_course, make_assignment, db_session
):
    teacher, student = make_user(Role.teacher), make_user(Role.student)
    course = make_course(teacher, students=[student])
    assignment = make_assignment(course)
    db_session.add(Submission(assignment_id=assignment.id, student_id=student.id, code="print(1)"))
    db_session.commit()

    removed = client.delete(
        f"{API}/courses/{course.id}/students/{student.id}", headers=auth(teacher)
    )

    assert removed.status_code == 204
    assert db_session.get(Enrollment, (student.id, course.id)) is None
    assert client.get(f"{API}/courses/{course.id}", headers=auth(student)).status_code == 404
    db_session.expire_all()
    assert db_session.query(Submission).filter_by(student_id=student.id).count() == 1


def test_a_student_leaves_a_course(client, auth, make_user, make_course):
    teacher, student = make_user(Role.teacher), make_user(Role.student)
    course = make_course(teacher, students=[student])

    left = client.delete(f"{API}/courses/{course.id}/enrollment", headers=auth(student))
    again = client.delete(f"{API}/courses/{course.id}/enrollment", headers=auth(student))

    assert (left.status_code, again.status_code) == (204, 404)
    assert client.get(f"{API}/courses", headers=auth(student)).json() == []
