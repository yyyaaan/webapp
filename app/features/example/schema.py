from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TodoItemCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TodoItemResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
