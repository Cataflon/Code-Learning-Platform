"""Routes of the technical admin (decision D30). Every route needs the admin role."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.core.deps import AdminUser, DbSession
from app.models import Role
from app.schemas.admin import (
    AdminStats,
    AdminUserPage,
    AdminUserRead,
    AdminUserUpdate,
    InviteCodeCreate,
    InviteCodeRead,
    TemporaryPassword,
)
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
def get_stats(db: DbSession, _admin: AdminUser):
    return admin_service.stats(db)


@router.get("/users", response_model=AdminUserPage)
def list_users(
    db: DbSession,
    _admin: AdminUser,
    q: Annotated[str, Query(max_length=100)] = "",
    role: Role | None = None,
    active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return admin_service.list_users(db, q, role, active, limit, offset)


@router.patch("/users/{user_id}", response_model=AdminUserRead)
def update_user(user_id: int, data: AdminUserUpdate, db: DbSession, admin: AdminUser):
    user = admin_service.update_user(db, admin, admin_service.get_user(db, user_id), data)
    return admin_service.read_user(db, user)


@router.post("/users/{user_id}/reset-password", response_model=TemporaryPassword)
def reset_password(user_id: int, db: DbSession, admin: AdminUser):
    user = admin_service.get_user(db, user_id)
    return TemporaryPassword(temporary_password=admin_service.reset_password(db, admin, user))


@router.get("/invite-codes", response_model=list[InviteCodeRead])
def list_invite_codes(db: DbSession, _admin: AdminUser):
    return admin_service.list_invite_codes(db)


@router.post("/invite-codes", response_model=InviteCodeRead, status_code=201)
def create_invite_code(data: InviteCodeCreate, db: DbSession, admin: AdminUser):
    return admin_service.create_invite_code(db, admin, data)


@router.post("/invite-codes/{invite_id}/revoke", response_model=InviteCodeRead)
def revoke_invite_code(invite_id: int, db: DbSession, _admin: AdminUser):
    return admin_service.revoke_invite_code(db, invite_id)
