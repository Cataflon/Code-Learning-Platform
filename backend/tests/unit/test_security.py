from datetime import timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.models import Role, User


def make_user() -> User:
    return User(id=7, email="a@example.com", full_name="A", password_hash="x", role=Role.teacher)


def test_same_password_gives_different_hashes():
    first, second = hash_password("parola123"), hash_password("parola123")

    assert first != second  # a random salt is mixed into every hash
    assert first.startswith("$argon2")


def test_verify_password_accepts_right_and_rejects_wrong():
    hashed = hash_password("parola123")

    assert verify_password("parola123", hashed) is True
    assert verify_password("parola124", hashed) is False
    assert verify_password("parola123", "!unusable") is False


def test_token_carries_user_id_and_role():
    payload = decode_token(create_access_token(make_user()))

    assert payload["sub"] == "7"
    assert payload["role"] == "teacher"
    assert "exp" in payload


def test_expired_token_is_rejected():
    token = create_access_token(make_user(), expires_in=timedelta(seconds=-1))

    with pytest.raises(UnauthorizedError):
        decode_token(token)


def test_tampered_token_is_rejected():
    token = create_access_token(make_user())
    header, payload, signature = token.split(".")
    forged_payload = jwt.utils.base64url_encode(b'{"sub":"1","role":"teacher"}').decode()

    with pytest.raises(UnauthorizedError):
        decode_token(f"{header}.{forged_payload}.{signature}")


def test_token_signed_with_another_secret_is_rejected():
    settings = get_settings()
    token = jwt.encode(
        {"sub": "7", "exp": 9999999999}, "another-secret-another-secret-123", "HS256"
    )

    assert settings.jwt_secret != "another-secret-another-secret-123"
    with pytest.raises(UnauthorizedError):
        decode_token(token)
