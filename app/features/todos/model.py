from pydantic import Field
from app.models.base import MongoBaseModel


class TodoItem(MongoBaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    content: str | None = Field(default=None, max_length=5000)  # Detailed content/notes
    completed: bool = False
    column_width: int = Field(default=12, ge=1, le=12)  # Bootstrap column width (1-12)
    order: int = 0  # For sorting within columns
