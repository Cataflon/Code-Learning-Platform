"""What the technical admin reads and sends (decision D30)."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import Role


class AdminUserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime
    courses_taught: int
    courses_enrolled: int
    submissions: int
    invite_code: str | None  # the code a teacher registered with


class AdminUserPage(BaseModel):
    items: list[AdminUserRead]
    total: int


class AdminUserUpdate(BaseModel):
    role: Role | None = None
    is_active: bool | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=120)


class TemporaryPassword(BaseModel):
    """Shown once to the admin, who passes it on; the user changes it from Profile."""

    temporary_password: str


class InviteCodeCreate(BaseModel):
    note: str = Field(default="", max_length=200)
    max_uses: int = Field(default=1, ge=1, le=100)
    expires_in_days: int | None = Field(default=14, ge=1, le=365)  # None = never


class InviteCodeRead(BaseModel):
    id: int
    code: str
    note: str
    max_uses: int
    uses: int
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    created_by_name: str | None
    status: str  # active | used | expired | revoked
    used_by: list[str]  # names of the teachers who registered with it


class AdminStats(BaseModel):
    students: int
    teachers: int
    admins: int
    disabled: int
    courses: int
    assignments: int
    submissions: int
    active_invite_codes: int
