# MongoDB Access Patterns: Collection Style vs Model Style

## Collection Style (Recommended for this project)

**What we're using now:**

```python
# Direct motor collection access
db = get_database()
user = await db.users.find_one({"_id": ObjectId(user_id)})
await db.users.insert_one({"name": "John", "email": "john@example.com"})
```

**Advantages:**
- Simpler, less abstraction
- Direct control over queries
- Works natively with Motor's async API
- No ODM overhead or magic
- Pydantic handles validation separately

**Disadvantages:**
- Need to manually convert ObjectId to strings
- No built-in relationship handling (not relevant for MongoDB anyway)

## Model Style (ODM)

**What this looks like (using Beanie/MongoEngine):**

```python
class User(Document):
    name: str
    email: str = EmailField()

# Usage
user = await User.find_one(User.id == user_id)
await User(name="John", email="john@example.com").insert()
```

**Advantages:**
- Cleaner looking code
- Built-in validation
- Reference fields
- Query builder syntax

**Disadvantages:**
- Another layer to learn/debug
- Magic behavior can be confusing
- Performance overhead
- MongoDB is schemaless - ODM fights this design

## Recommendation for This Project

**Use Collection Style** for these reasons:

1. **You're fluent with Motor** - no need to learn another layer
2. **Pydantic provides validation** - models are for validation, not database access
3. **MongoDB's strength is schema flexibility** - ODMs try to enforce schemas
4. **Simpler debugging** - see exactly what queries are being sent
5. **Better performance** - no conversion overhead

## Improvements Made

### 1. Collection Helper (`app/core/collections.py`)

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

# Usage
users_collection = CollectionHelper("users")
await users_collection.collection.find_one({"email": "test@example.com"})
```

### 2. Updated PyObjectId for Pydantic v2

```python
class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler) -> core_schema.CoreSchema:
        # Proper Pydantic v2 validation
```

### 3. Modern Python Syntax Updates

- `Optional[str]` → `str | None`
- `List[str]` → `list[str]`
- `Dict[str, Any]` → `dict[str, Any]`
- `datetime.utcnow()` → `datetime.now(timezone.utc)`

### 4. Simplified Auth Router

- Removed unused imports
- Direct collection access via motor
- Cleaner error handling
