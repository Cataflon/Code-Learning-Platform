import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Role(enum.StrEnum):
    student = "student"
    teacher = "teacher"
    # Technical administrator: manages accounts and invite codes, not courses (decision D30).
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)  # stored lowercase
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False, length=16))
    # A disabled account cannot sign in and its tokens stop working; its data stays.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # The invite code a teacher registered with (kept for the admin's overview).
    invite_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("invite_codes.id", ondelete="SET NULL", name="users_invite_code_id_fkey"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InviteCode(Base):
    """A code an admin hands to a future teacher; registering as a teacher needs one (D30)."""

    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # stored uppercase
    note: Mapped[str] = mapped_column(String(200), default="")  # who it is for
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    uses: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id", ondelete="SET NULL", use_alter=True, name="invite_codes_created_by_fkey"
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
