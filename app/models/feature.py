from pydantic import Field
from app.models.base import MongoBaseModel


class FeatureModel(MongoBaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    enabled: bool = True
