from pydantic import BaseModel
from enum import Enum


class UserRole(str, Enum):
    """User roles for permission management"""
    ADMIN = "admin"
    USER = "user"


class AuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: str | None = None
    role: str = "user"
    provider: str


class AuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: str | None = None
    provider: str
