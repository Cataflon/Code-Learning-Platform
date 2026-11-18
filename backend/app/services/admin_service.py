"""The technical admin: accounts and invite codes (decision D30).

The admin does not see course content (tasks, code, grades); they manage who can sign in and
who may register as a teacher. Rules that keep the platform usable:

* an admin cannot disable themselves or take away their own admin role;
* the last active admin cannot be disabled or demoted;
* a teacher who still owns courses cannot become a student (the courses would have no owner).
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, InvalidDataError, NotFoundError
from app.core.security import hash_password
from app.models import (
    Assignment,
    Course,
    Enrollment,
    InviteCode,
    Role,
    Submission,
    User,
)
from app.schemas.admin import (
    AdminStats,
    AdminUserPage,
    AdminUserRead,
    AdminUserUpdate,
    InviteCodeCreate,
    InviteCodeRead,
)

# No 0/O or 1/I/L, so a code read aloud or copied by hand is not mistyped.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


# --- users -----------------------------------------------------------------------------------


def _counts(db: Session, user_ids: list[int]) -> dict[str, dict[int, int]]:
    if not user_ids:
        return {"taught": {}, "enrolled": {}, "submissions": {}}

    def grouped(column, model):
        rows = db.execute(select(column, func.count()).where(column.in_(user_ids)).group_by(column))
        return dict(rows.all())

    return {
        "taught": grouped(Course.teacher_id, Course),
        "enrolled": grouped(Enrollment.user_id, Enrollment),
        "submissions": grouped(Submission.student_id, Submission),
    }


def _read(user: User, counts: dict, codes: dict[int, str]) -> AdminUserRead:
    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        courses_taught=counts["taught"].get(user.id, 0),
        courses_enrolled=counts["enrolled"].get(user.id, 0),
        submissions=counts["submissions"].get(user.id, 0),
        invite_code=codes.get(user.invite_code_id) if user.invite_code_id else None,
    )


def _codes_of(db: Session, users: list[User]) -> dict[int, str]:
    ids = {user.invite_code_id for user in users if user.invite_code_id}
    if not ids:
        return {}
    return dict(
        db.execute(select(InviteCode.id, InviteCode.code).where(InviteCode.id.in_(ids))).all()
    )


def list_users(
    db: Session,
    query: str = "",
    role: Role | None = None,
    active: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> AdminUserPage:
    conditions = []
    text = query.strip().lower()
    if text:
        pattern = f"%{text.replace('%', r'\%').replace('_', r'\_')}%"
        conditions.append(or_(User.email.ilike(pattern), func.lower(User.full_name).like(pattern)))
    if role is not None:
        conditions.append(User.role == role)
    if active is not None:
        conditions.append(User.is_active.is_(active))
    total = db.scalar(select(func.count()).select_from(User).where(*conditions))
    users = list(
        db.scalars(
            select(User)
            .where(*conditions)
            .order_by(User.created_at.desc(), User.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    counts = _counts(db, [user.id for user in users])
    codes = _codes_of(db, users)
    return AdminUserPage(items=[_read(user, counts, codes) for user in users], total=total)


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    return user


def read_user(db: Session, user: User) -> AdminUserRead:
    return _read(user, _counts(db, [user.id]), _codes_of(db, [user]))


def _active_admins(db: Session) -> int:
    return db.scalar(
        select(func.count()).select_from(User).where(User.role == Role.admin, User.is_active)
    )


def update_user(db: Session, admin: User, user: User, data: AdminUserUpdate) -> User:
    changes_role = data.role is not None and data.role != user.role
    disables = data.is_active is False and user.is_active
    if user.id == admin.id and (changes_role or disables):
        raise InvalidDataError("You cannot change your own role or disable your own account")
    if user.role == Role.admin and (changes_role or disables) and _active_admins(db) <= 1:
        raise ConflictError("This is the last active admin; make another admin first")
    if changes_role and user.role == Role.teacher:
        owned = db.scalar(
            select(func.count()).select_from(Course).where(Course.teacher_id == user.id)
        )
        if owned:
            raise ConflictError(
                f"This teacher still owns {owned} course(s); they must delete them first"
            )
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.full_name is not None:
        user.full_name = " ".join(data.full_name.split())
    db.commit()
    db.refresh(user)
    return user


def reset_password(db: Session, admin: User, user: User) -> str:
    """A new random password, returned once; the old one stops working at once."""
    if user.id == admin.id:
        raise InvalidDataError("Change your own password from Profile")
    password = "".join(secrets.choice(_ALPHABET.lower() + _ALPHABET) for _ in range(14))
    user.password_hash = hash_password(password)
    db.commit()
    return password


# --- invite codes ----------------------------------------------------------------------------


def _new_code(db: Session) -> str:
    while True:
        body = "".join(secrets.choice(_ALPHABET) for _ in range(8))
        code = f"TEACH-{body[:4]}-{body[4:]}"
        if db.scalar(select(InviteCode.id).where(InviteCode.code == code)) is None:
            return code


def status_of(invite: InviteCode, now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    if invite.revoked_at is not None:
        return "revoked"
    if invite.uses >= invite.max_uses:
        return "used"
    if invite.expires_at is not None and invite.expires_at <= now:
        return "expired"
    return "active"


def _read_invites(db: Session, invites: list[InviteCode]) -> list[InviteCodeRead]:
    ids = [invite.id for invite in invites]
    creators = {invite.created_by for invite in invites if invite.created_by}
    names = (
        dict(db.execute(select(User.id, User.full_name).where(User.id.in_(creators))).all())
        if creators
        else {}
    )
    used_by: dict[int, list[str]] = {}
    if ids:
        rows = db.execute(
            select(User.invite_code_id, User.full_name)
            .where(User.invite_code_id.in_(ids))
            .order_by(User.created_at)
        )
        for code_id, name in rows:
            used_by.setdefault(code_id, []).append(name)
    now = datetime.now(UTC)
    return [
        InviteCodeRead(
            id=invite.id,
            code=invite.code,
            note=invite.note,
            max_uses=invite.max_uses,
            uses=invite.uses,
            expires_at=invite.expires_at,
            revoked_at=invite.revoked_at,
            created_at=invite.created_at,
            created_by_name=names.get(invite.created_by),
            status=status_of(invite, now),
            used_by=used_by.get(invite.id, []),
        )
        for invite in invites
    ]


def list_invite_codes(db: Session) -> list[InviteCodeRead]:
    invites = list(
        db.scalars(select(InviteCode).order_by(InviteCode.created_at.desc(), InviteCode.id.desc()))
    )
    return _read_invites(db, invites)


def create_invite_code(db: Session, admin: User, data: InviteCodeCreate) -> InviteCodeRead:
    expires = (
        datetime.now(UTC) + timedelta(days=data.expires_in_days) if data.expires_in_days else None
    )
    invite = InviteCode(
        code=_new_code(db),
        note=" ".join(data.note.split()),
        max_uses=data.max_uses,
        uses=0,
        expires_at=expires,
        created_by=admin.id,
        created_at=datetime.now(UTC),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return _read_invites(db, [invite])[0]


def revoke_invite_code(db: Session, invite_id: int) -> InviteCodeRead:
    invite = db.get(InviteCode, invite_id)
    if invite is None:
        raise NotFoundError("Invite code not found")
    if invite.revoked_at is None:
        invite.revoked_at = datetime.now(UTC)
        db.commit()
        db.refresh(invite)
    return _read_invites(db, [invite])[0]


# --- overview --------------------------------------------------------------------------------


def stats(db: Session) -> AdminStats:
    by_role = dict(db.execute(select(User.role, func.count()).group_by(User.role)).all())
    now = datetime.now(UTC)
    active_codes = db.scalar(
        select(func.count())
        .select_from(InviteCode)
        .where(
            InviteCode.revoked_at.is_(None),
            InviteCode.uses < InviteCode.max_uses,
            or_(InviteCode.expires_at.is_(None), InviteCode.expires_at > now),
        )
    )
    count = lambda model: db.scalar(select(func.count()).select_from(model))  # noqa: E731
    return AdminStats(
        students=by_role.get(Role.student, 0),
        teachers=by_role.get(Role.teacher, 0),
        admins=by_role.get(Role.admin, 0),
        disabled=db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(False))),
        courses=count(Course),
        assignments=count(Assignment),
        submissions=count(Submission),
        active_invite_codes=active_codes,
    )
