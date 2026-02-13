from pydantic import Field
from app.models.base import MongoBaseModel


class TodoItem(MongoBaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = Field(default=None, max_length=500)
    completed: bool = False
