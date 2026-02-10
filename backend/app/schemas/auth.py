from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignupRequest(BaseModel):
    """Request model for user signup."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response model for authentication endpoints."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class LogoutRequest(BaseModel):
    """Request model for logout."""
    pass
