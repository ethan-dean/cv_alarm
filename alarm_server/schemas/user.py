"""Pydantic schemas for user-related operations."""
from pydantic import BaseModel, Field
from datetime import datetime


class UserLogin(BaseModel):
    """Schema for user login request."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for JWT token data (decoded payload)."""

    user_id: int
    username: str
