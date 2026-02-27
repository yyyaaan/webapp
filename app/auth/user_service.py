import os
from app.core.collections import users_collection
from app.core.security import create_access_token
from app.models.user import User, UserRole


async def find_or_create_user(provider: str, provider_id: str, email: str, name: str, avatar_url: str = None, role: UserRole = None) -> dict:
    """
    Find existing user or create a new one.
    Returns the user document with _id.
    
    Args:
        provider: OAuth provider (github, google, microsoft)
        provider_id: Unique ID from provider
        email: User email
        name: User display name
        avatar_url: Optional avatar URL
        role: User role (default: determined by ADMIN_EMAILS env var, else USER)
    """
    collection = users_collection.collection
    
    # Find existing user
    user = await collection.find_one({
        "provider": provider,
        "provider_id": provider_id,
    })
    
    if user:
        return user
    
    # Determine role: use provided role, or check ADMIN_EMAILS env var
    if role is None:
        admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
        admin_emails = [e.strip().lower() for e in admin_emails if e.strip()]
        
        # Grant admin if email is in ADMIN_EMAILS
        if email and email.lower() in admin_emails:
            role = UserRole.ADMIN
        else:
            role = UserRole.USER
    
    # Create new user with determined role
    user_data = User(
        email=email or f"{provider}@local",
        name=name or "User",
        provider=provider,
        provider_id=provider_id,
        avatar_url=avatar_url,
        role=role,
    )
    user_dict = user_data.model_dump(by_alias=True, exclude_none=True)
    user_dict.pop('_id', None)
    
    result = await collection.insert_one(user_dict)
    user = await collection.find_one({"_id": result.inserted_id})
    
    return user


def create_user_token(user: dict) -> str:
    """Create JWT token for user including role"""
    return create_access_token(data={
        "sub": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name", "User"),
        "role": user.get("role", "user"),  # Include role in token
    })
