"""Registration, sign-in and profile changes."""

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import BadRequestError, ConflictError, PermissionDeniedError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models import Role, User
from app.schemas.auth import PasswordChange, RegisterRequest, UserUpdate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def register_user(db: Session, data: RegisterRequest) -> User:
    if data.role == Role.teacher:
        expected = get_settings().teacher_invite_code
        # compare_digest avoids leaking, through timing, how much of the code matched.
        if not data.invite_code or not secrets.compare_digest(data.invite_code, expected):
            raise PermissionDeniedError("A valid invite code is required for a teacher account")
    email = data.email.strip().lower()
    if get_user_by_email(db, email) is not None:
        raise ConflictError("An account with this email already exists")
    user = User(
        email=email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    # Same message for an unknown email and a wrong password, so emails cannot be probed.
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Incorrect email or password")
    return user


def update_profile(db: Session, user: User, data: UserUpdate) -> User:
    user.full_name = data.full_name
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, data: PasswordChange) -> None:
    if not verify_password(data.current_password, user.password_hash):
        raise BadRequestError("The current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    db.commit()
