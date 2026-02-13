from pydantic import EmailStr, Field
from app.models.base import MongoBaseModel


class User(MongoBaseModel):
    email: EmailStr
    name: str
    provider: str
    provider_id: str
    avatar_url: str | None = None
    is_active: bool = True
