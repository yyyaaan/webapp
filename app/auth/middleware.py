from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from typing import Optional
from app.core.security import decode_access_token
from app.auth.header_auth import header_auth_manager


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Get current user from multiple authentication sources:
    1. JWT token from cookies (OAuth flow)
    2. Header-based authentication (Databricks/Azure App Service)
    
    Returns user dict with id, email, name, role, and auth_method.
    """
    # First try JWT token from cookies (OAuth flow)
    token = request.cookies.get("access_token")
    if token:
        payload = decode_access_token(token)
        if payload:
            return {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "role": payload.get("role", "user"),  # Include role
                "auth_method": "oauth"
            }
    
    # Then try header-based authentication
    header_token = await header_auth_manager.authenticate_from_headers(request)
    if header_token:
        payload = decode_access_token(header_token)
        if payload:
            return {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "role": payload.get("role", "user"),  # Include role
                "auth_method": "header"
            }
    
    return None


async def require_auth(request: Request) -> dict:
    """
    Require authentication and return user info.
    Raises HTTPException if not authenticated.
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_admin(request: Request) -> dict:
    """
    Require admin role and return user info.
    Raises HTTPException if not authenticated or not admin.
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def get_auth_method_for_request(request: Request) -> str:
    """
    Determine the best authentication method for this request.
    Used to decide which login options to show.
    """
    # Check if header auth is available and enabled
    if (request.headers.get("X-Databricks-User-Email") or 
        request.headers.get("X-MS-CLIENT-PRINCIPAL")):
        return "header"
    
    # Default to OAuth
    return "oauth"


def get_available_auth_providers(request: Request) -> list[str]:
    """
    Get list of available authentication providers for this request.
    """
    from app.core.config import get_settings
    from app.auth.providers import registry
    
    settings = get_settings()
    providers = []
    
    # OAuth providers
    oauth_providers = registry.list_providers()
    if oauth_providers:
        providers.extend(oauth_providers)
    
    # Header-based providers (if headers are present)
    if settings.databricks_header_auth and request.headers.get("X-Databricks-User-Email"):
        providers.append("databricks")
    
    if settings.azure_app_service_auth and request.headers.get("X-MS-CLIENT-PRINCIPAL"):
        providers.append("azure_app_service")
    
    return providers


class AuthMiddleware:
    """
    Middleware to handle authentication across different methods.
    This can be used as a dependency in FastAPI routes.
    """
    
    def __init__(self, require_auth: bool = False):
        self.require_auth = require_auth
    
    async def __call__(self, request: Request) -> Optional[dict]:
        user = await get_current_user(request)
        if self.require_auth and not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        return user
