"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, repr=False)
    full_name: str = Field(..., min_length=1)
    country: str | None = None

    @field_validator("username", "full_name")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = value.strip(" ")
        if not value:
            raise ValueError("Must not be blank")
        return value


class UserLoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str = Field(repr=False)


class UserResponse(BaseModel):
    """Response schema for user information (no sensitive data)."""

    id: UUID
    email: str
    username: str
    full_name: str
    country: str | None
    is_super_admin: bool
    email_verified_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """Response schema for successful login."""

    access_token: str = Field(repr=False)
    refresh_token: str = Field(repr=False)
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str = Field(min_length=1, max_length=4096, repr=False)
