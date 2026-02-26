from app.core.collections import users_collection
from app.core.security import create_access_token
from app.models.user import User


async def find_or_create_user(provider: str, provider_id: str, email: str, name: str, avatar_url: str = None) -> dict:
    """
    Find existing user or create a new one.
    Returns the user document with _id.
    """
    collection = users_collection.collection
    
    # Find existing user
    user = await collection.find_one({
        "provider": provider,
        "provider_id": provider_id,
    })
    
    if user:
        return user
    
    # Create new user
    user_data = User(
        email=email or f"{provider}@local",
        name=name or "User",
        provider=provider,
        provider_id=provider_id,
        avatar_url=avatar_url,
    )
    user_dict = user_data.model_dump(by_alias=True, exclude_none=True)
    user_dict.pop('_id', None)
    
    result = await collection.insert_one(user_dict)
    user = await collection.find_one({"_id": result.inserted_id})
    
    return user


def create_user_token(user: dict) -> str:
    """Create JWT token for user"""
    return create_access_token(data={
        "sub": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name", "User")
    })
