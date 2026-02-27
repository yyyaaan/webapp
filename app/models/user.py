from pydantic import EmailStr, Field
from enum import Enum
from app.models.base import MongoBaseModel


class UserRole(str, Enum):
    """User roles for permission management"""
    ADMIN = "admin"
    USER = "user"


class User(MongoBaseModel):
    email: EmailStr
    name: str
    provider: str
    provider_id: str
    avatar_url: str | None = None
    role: UserRole = UserRole.USER  # Default role is USER
    is_active: bool = True
