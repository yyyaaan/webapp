from fastapi import APIRouter, HTTPException, Query, Request
import secrets

from app.core.collections import users_collection
from app.core.security import create_access_token
from app.core.security import create_access_token
from app.core.config import get_settings
from app.auth.providers import registry, OAuthProviderConfig
from app.auth.github import GitHubOAuthProvider
from app.auth.google import GoogleOAuthProvider
from app.auth.microsoft import MicrosoftOAuthProvider
from app.auth.schemas import AuthUrlResponse, TokenResponse, UserResponse
from app.models.user import User
from app.auth.header_auth import header_auth_manager
from bson import ObjectId
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def init_oauth_providers():
    if settings.github_client_id and settings.github_client_secret:
        registry.register(
            "github",
            GitHubOAuthProvider(
                OAuthProviderConfig(
                    client_id=settings.github_client_id,
                    client_secret=settings.github_client_secret,
                    authorize_url="https://github.com/login/oauth/authorize",
                    access_token_url="https://github.com/login/oauth/access_token",
                    user_info_url="https://api.github.com/user",
                    scope="user:email",
                )
            ),
        )

    if settings.google_client_id and settings.google_client_secret:
        registry.register(
            "google",
            GoogleOAuthProvider(
                OAuthProviderConfig(
                    client_id=settings.google_client_id,
                    client_secret=settings.google_client_secret,
                    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
                    access_token_url="https://oauth2.googleapis.com/token",
                    user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
                    scope="openid email profile",
                )
            ),
        )

    if settings.microsoft_client_id and settings.microsoft_client_secret:
        registry.register(
            "microsoft",
            MicrosoftOAuthProvider(
                OAuthProviderConfig(
                    client_id=settings.microsoft_client_id,
                    client_secret=settings.microsoft_client_secret,
                    authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                    access_token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    user_info_url="https://graph.microsoft.com/v1.0/me",
                    scope="openid email profile",
                )
            ),
        )


@router.get("/providers")
async def list_providers():
    return {"providers": registry.list_providers()}


@router.get("/login/{provider}", response_model=AuthUrlResponse)
async def login(provider: str):
    provider_client = registry.get(provider)
    if not provider_client:
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' not configured")

    state = secrets.token_urlsafe(32)
    redirect_uri = f"{settings.frontend_url}/auth/callback/{provider}"
    auth_url = provider_client.get_authorization_url(redirect_uri, state)

    return {"auth_url": auth_url, "state": state}


@router.get("/callback/{provider}", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
):
    collection = users_collection.collection
    provider_client = registry.get(provider)

    user = await collection.find_one(
        {
            "provider": provider,
            "provider_id": user_info.get("id") or "unknown",
        }
    )

    if not user:
        user_data = User(
            email=user_info.get("email") or f"{provider}@local",
            name=user_info.get("name") or "User",
            avatar_url=user_info.get("avatar_url"),
            provider=provider,
            provider_id=user_info.get("id") or "unknown",
        )
        # Exclude _id when None to let MongoDB auto-generate ObjectId
        user_dict = user_data.model_dump(by_alias=True, exclude_none=True)
        user_dict.pop('_id', None)
        result = await collection.insert_one(user_dict)
        user = await collection.find_one({"_id": result.inserted_id})

    jwt_token = create_access_token(data={"sub": str(user["_id"]), "email": user["email"]})

    return HTMLResponse(f"""
    <script>
        document.cookie = "access_token={jwt_token}; path=/; max-age={7*24*60*60}";
        window.location.href = "/";
    </script>
    """)


@router.get("/header-login", response_class=HTMLResponse)
async def header_login():
    """
    Endpoint to handle header-based authentication redirect.
    This can be used when headers are present but user needs to be redirected to set the cookie.
    """
    return HTMLResponse("""
    <script>
        // Try to reload the page to trigger header authentication
        window.location.href = "/";
    </script>
    """)


@router.get("/providers")
async def list_providers_with_headers(request: Request):
    """
    List all available providers including header-based ones for the current request.
    """
    from app.auth.middleware import get_available_auth_providers
    
    providers = get_available_auth_providers(request)
    return {"providers": providers}
