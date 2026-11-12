from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.auth import PasswordChange, UserRead, UserUpdate
from app.services import auth_service

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
