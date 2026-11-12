from app.core.config import get_settings
from app.models import Role

API = "/api/v1"
REGISTRATION = {
    "email": "Ana.Pop@Example.com",
    "full_name": "  Ana   Pop ",
    "password": "parola123",
}


def login(client, email, password):
    return client.post(f"{API}/auth/login", data={"username": email, "password": password})


def test_register_creates_student_and_never_returns_password(client):
    response = client.post(f"{API}/auth/register", json=REGISTRATION)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana.pop@example.com"  # stored lowercase
    assert body["full_name"] == "Ana Pop"
    assert body["role"] == "student"
    assert not any("password" in key for key in body)


def test_register_duplicate_email_returns_409(client):
    client.post(f"{API}/auth/register", json=REGISTRATION)

    response = client.post(
        f"{API}/auth/register", json={**REGISTRATION, "email": "ana.pop@example.com"}
    )

    assert response.status_code == 409


def test_register_short_password_returns_422(client):
    response = client.post(f"{API}/auth/register", json={**REGISTRATION, "password": "short"})

    assert response.status_code == 422


def test_register_teacher_requires_invite_code(client):
    teacher = {**REGISTRATION, "role": "teacher"}

    without_code = client.post(f"{API}/auth/register", json=teacher)
    wrong_code = client.post(f"{API}/auth/register", json={**teacher, "invite_code": "nope"})
    right_code = client.post(
        f"{API}/auth/register",
        json={**teacher, "invite_code": get_settings().teacher_invite_code},
    )

    assert without_code.status_code == 403
    assert wrong_code.status_code == 403
    assert right_code.status_code == 201
    assert right_code.json()["role"] == "teacher"


def test_login_returns_token_that_opens_users_me(client, make_user):
    user = make_user(Role.student, password="parola123", email="ana@example.com")

    response = login(client, "ANA@example.com", "parola123")

    assert response.status_code == 200
    token = response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"
    me = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["id"] == user.id


def test_login_with_wrong_password_or_unknown_email_returns_401(client, make_user):
    make_user(Role.student, password="parola123", email="ana@example.com")

    wrong_password = login(client, "ana@example.com", "gresita123")
    unknown_email = login(client, "nobody@example.com", "parola123")

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_users_me_without_or_with_bad_token_returns_401(client):
    missing = client.get(f"{API}/users/me")
    garbage = client.get(f"{API}/users/me", headers={"Authorization": "Bearer not-a-token"})

    assert missing.status_code == 401
    assert missing.json()["code"] == "unauthorized"
    assert missing.headers["WWW-Authenticate"] == "Bearer"
    assert garbage.status_code == 401


def test_update_full_name(client, auth, student):
    response = client.patch(
        f"{API}/users/me", json={"full_name": "New Name"}, headers=auth(student)
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"


def test_change_password_requires_the_current_one(client, auth, make_user):
    user = make_user(Role.student, password="parola123", email="ana@example.com")
    url = f"{API}/users/me/password"

    wrong = client.post(
        url,
        json={"current_password": "gresita123", "new_password": "nouaparola1"},
        headers=auth(user),
    )
    right = client.post(
        url,
        json={"current_password": "parola123", "new_password": "nouaparola1"},
        headers=auth(user),
    )

    assert wrong.status_code == 400
    assert right.status_code == 204
    assert login(client, "ana@example.com", "parola123").status_code == 401
    assert login(client, "ana@example.com", "nouaparola1").status_code == 200
