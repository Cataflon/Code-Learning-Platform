"""Password hashing (Argon2) and JWT access tokens."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.models import User

_password_hash = PasswordHash.recommended()  # Argon2id with a random salt per hash


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hash.verify(password, password_hash)
    except Exception:  # unknown or malformed hash (for example a seeded placeholder)
        return False


def create_access_token(user: User, expires_in: timedelta | None = None) -> str:
    """Signed token carrying the user id (sub), the role and the expiry time."""
    settings = get_settings()
    lifetime = expires_in or timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "exp": datetime.now(UTC) + lifetime,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Return the payload, or raise 401 if the token is expired, altered or malformed."""
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Your session has expired, sign in again") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid authentication token") from exc
