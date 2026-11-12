from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.auth import PasswordChange, UserRead, UserUpdate
from app.schemas.dashboard import Activity
from app.services import auth_service, dashboard_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserRead)
def update_me(data: UserUpdate, user: CurrentUser, db: DbSession):
    return auth_service.update_profile(db, user, data)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(data: PasswordChange, user: CurrentUser, db: DbSession) -> None:
    auth_service.change_password(db, user, data)


@router.get("/me/activity", response_model=Activity)
def read_my_activity(
    user: CurrentUser, db: DbSession, weeks: Annotated[int, Query(ge=1, le=52)] = 14
):
    """Submissions per day for the activity grid on the profile page, plus totals."""
    return dashboard_service.user_activity(db, user, weeks)
