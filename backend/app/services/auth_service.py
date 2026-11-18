"""Registration, sign-in and profile changes."""

import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import BadRequestError, ConflictError, PermissionDeniedError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models import InviteCode, Role, User
from app.schemas.auth import PasswordChange, RegisterRequest, UserUpdate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


INVALID_INVITE = "A valid invite code is required for a teacher account"


def _use_invite_code(db: Session, given: str | None) -> InviteCode | None:
    """Check a teacher's invite code and count the use (decision D30).

    Codes made by an admin are checked first; the code from the settings
    (``TEACHER_INVITE_CODE``) still works when it is set, so a fresh install has a way in.
    Returns the admin's code that was used, or None for the code from the settings.
    """
    code = (given or "").strip().upper()
    if not code:
        raise PermissionDeniedError(INVALID_INVITE)
    invite = db.scalar(
        select(InviteCode).where(InviteCode.code == code).with_for_update()
    )  # locked, so two registrations cannot both take the last use
    if invite is not None:
        expired = invite.expires_at is not None and invite.expires_at <= datetime.now(UTC)
        if invite.revoked_at is not None or expired or invite.uses >= invite.max_uses:
            raise PermissionDeniedError("This invite code has expired or was already used")
        invite.uses += 1
        return invite
    fallback = get_settings().teacher_invite_code.strip().upper()
    # compare_digest avoids leaking, through timing, how much of the code matched.
    if fallback and secrets.compare_digest(code, fallback):
        return None
    raise PermissionDeniedError(INVALID_INVITE)


def register_user(db: Session, data: RegisterRequest) -> User:
    if data.role == Role.admin:
        raise PermissionDeniedError("Admin accounts are created by another admin")
    email = data.email.strip().lower()
    if get_user_by_email(db, email) is not None:
        raise ConflictError("An account with this email already exists")
    invite = _use_invite_code(db, data.invite_code) if data.role == Role.teacher else None
    user = User(
        email=email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=data.role,
        invite_code_id=invite.id if invite else None,
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
    if not user.is_active:
        raise PermissionDeniedError("This account has been disabled. Contact the administrator.")
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
