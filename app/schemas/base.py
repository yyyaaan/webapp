from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Generic, TypeVar

ModelType = TypeVar("ModelType")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(BaseSchema):
    id: str
    created_at: datetime
    updated_at: datetime | None = None


class PaginatedResponse(BaseSchema, Generic[ModelType]):
    items: list[ModelType]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseSchema):
    error: str
    message: str
    detail: str | None = None
