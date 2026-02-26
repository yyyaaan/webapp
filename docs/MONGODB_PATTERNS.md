# MongoDB Patterns Guide

This document describes the MongoDB patterns used in this project.

## Collection Style (Recommended)

This project uses the **Collection Helper pattern** for MongoDB access:

```python
from app.core.collections import users_collection, todos_collection

# Find user
user = await users_collection.collection.find_one({"email": "test@example.com"})

# Insert document
await todos_collection.collection.insert_one({"title": "My todo", "completed": False})
```

### Collection Helper (`app/core/collections.py`)

```python
class CollectionHelper:
    def __init__(self, collection_name: str):
        self._collection_name = collection_name
        self._collection: AsyncIOMotorCollection | None = None

    @property
    def collection(self) -> AsyncIOMotorCollection:
        if self._collection is None:
            self._collection = get_collection(self._collection_name)
        return self._collection

# Pre-defined collections
users_collection = CollectionHelper("users")
todos_collection = CollectionHelper("todo_items")
features_collection = CollectionHelper("features")
```

### Benefits

- **Lazy initialization**: Collection is only accessed when needed
- **Centralized**: All collection names defined in one place
- **Type-safe**: Uses Motor's async API directly
- **Simple**: No ODM overhead

## Model Validation (Pydantic)

Models are used for **validation only**, not database access:

```python
from app.features.todos.model import TodoItem

# Create validated model
todo = TodoItem(
    title="My task",
    description="Task description",
    content="Detailed notes...",
    column_width=6,
)

# Convert to dict (exclude None and _id)
todo_dict = todo.model_dump(by_alias=True, exclude_none=True)
todo_dict.pop('_id', None)

# Insert
await todos_collection.collection.insert_one(todo_dict)
```

## Common Patterns

### Find or Create User

```python
from app.auth.user_service import find_or_create_user, create_user_token

# Find or create user
user = await find_or_create_user(
    provider="github",
    provider_id="12345",
    email="user@example.com",
    name="John Doe",
    avatar_url="https://...",
)

# Create JWT token
token = create_user_token(user)
```

### Query with Sorting

```python
# Get all todos sorted by order
todos = await todos_collection.collection.find({}).sort("order", 1).to_list(length=100)
```

### Update Document

```python
from datetime import datetime, timezone
from bson import ObjectId

await todos_collection.collection.update_one(
    {"_id": ObjectId(todo_id)},
    {"$set": {"completed": True, "updated_at": datetime.now(timezone.utc)}}
)
```

## PyObjectId for Pydantic v2

```python
from app.models.base import PyObjectId

class TodoItem(MongoBaseModel):
    id: PyObjectId | None = Field(None, alias="_id")
```

This provides proper validation for MongoDB ObjectId fields in Pydantic models.
