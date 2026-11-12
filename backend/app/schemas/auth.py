from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import Role

MIN_PASSWORD_LENGTH = 8


def _clean_name(value: str) -> str:
    value = " ".join(value.split())
    if not value:
        raise ValueError("must not be empty")
    return value


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)
    role: Role = Role.student
    invite_code: str | None = Field(default=None, max_length=64)  # required for teachers

    _clean_full_name = field_validator("full_name")(_clean_name)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    """Public profile. There is deliberately no password field of any kind here."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: Role
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)

    _clean_full_name = field_validator("full_name")(_clean_name)


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)
