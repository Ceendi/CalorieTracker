import uuid
from typing import Optional

from fastapi_users import schemas
from pydantic import EmailStr, field_validator


def validate_strong_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError(f"Password must be at least 8 characters long")
    if not any(char.isdigit() for char in v):
        raise ValueError(f"Password must contain at least one digit")
    if not any(char.isupper() for char in v):
        raise ValueError(f"Password must contain at least one uppercase letter")
    return v


class UserRead(schemas.BaseUser[uuid.UUID]):
    is_onboarded: bool
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    password: str

    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None

    @field_validator("password")
    def valid_password(cls, v: str):
        return validate_strong_password(v)


class UserUpdate(schemas.BaseUserUpdate):
    is_onboarded: Optional[bool] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None

    @field_validator("email", "is_superuser", "is_active", "is_verified", check_fields=False)
    def forbid_sensitive_updates(cls, v):
        if v is not None:
            raise ValueError("Cannot update this field")
        return v

    @field_validator("password")
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_strong_password(v)
        return v


class GoogleLogin(schemas.BaseModel):
    token: str


class ChangePassword(schemas.BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    def valid_password(cls, v: str):
        return validate_strong_password(v)
