"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    country: str | None = None


class UserLoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str


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
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Response schema for successful login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
