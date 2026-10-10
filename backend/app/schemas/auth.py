import uuid
from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=256)
    display_name: str | None = Field(default=None, max_length=120)

    @field_validator("display_name")
    @classmethod
    def _clean_name(cls, v: str | None) -> str | None:
        v = v.strip() if v else v
        return v or None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=256)


class RefreshRequest(BaseModel):
    # Mobile apps send the token in the body. The website uses an HttpOnly cookie instead.
    refresh_token: str | None = Field(default=None, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int  # seconds
    refresh_token: str | None = None  # present for mobile clients only


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None
    email_verified: bool
    roles: list[str]
    created_at: datetime


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)

    @field_validator("display_name")
    @classmethod
    def _clean_name(cls, v: str | None) -> str | None:
        v = v.strip() if v else v
        return v or None


class PreferencesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language: Literal["en", "ur"]
    arabic_font_size: int
    reminders_enabled: bool
    reminder_time: time | None


class PreferencesUpdate(BaseModel):
    language: Literal["en", "ur"] | None = None
    arabic_font_size: int | None = Field(default=None, ge=14, le=64)
    reminders_enabled: bool | None = None
    reminder_time: time | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(max_length=256)
    new_password: str = Field(max_length=256)


class DeleteAccountRequest(BaseModel):
    password: str = Field(max_length=256)


class RoleChange(BaseModel):
    role: Literal["user", "editor", "admin"]
