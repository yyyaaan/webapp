from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.database import get_collection


class CollectionHelper:
    def __init__(self, collection_name: str):
        self._collection_name = collection_name
        self._collection: AsyncIOMotorCollection | None = None

    @property
    def collection(self) -> AsyncIOMotorCollection:
        if self._collection is None:
            self._collection = get_collection(self._collection_name)
        return self._collection


users_collection = CollectionHelper("users")
todos_collection = CollectionHelper("todo_items")
features_collection = CollectionHelper("features")
