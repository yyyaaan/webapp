from fastapi import APIRouter, HTTPException, Query, Request
import secrets

from app.core.config import get_settings
from app.auth.providers import registry, OAuthProviderConfig
from app.auth.github import GitHubOAuthProvider
from app.auth.google import GoogleOAuthProvider
from app.auth.microsoft import MicrosoftOAuthProvider
from app.auth.schemas import AuthUrlResponse, TokenResponse, UserResponse
from app.auth.user_service import find_or_create_user, create_user_token
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def init_oauth_providers():
    """Initialize OAuth providers based on config"""
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
async def list_providers(request: Request):
    """List all available authentication providers"""
    from app.auth.middleware import get_available_auth_providers
    providers = get_available_auth_providers(request)
    return {"providers": providers}


@router.get("/login/{provider}", response_model=AuthUrlResponse)
async def login(provider: str):
    """Start OAuth login flow"""
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
    """Handle OAuth callback and create session"""
    provider_client = registry.get(provider)

    if not provider_client:
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' not configured")

    # Exchange code for access token
    token_data = await provider_client.exchange_code_for_token(
        code, f"{settings.frontend_url}/auth/callback/{provider}"
    )
    access_token = token_data.get("access_token")

    # Get user info from OAuth provider
    user_info = await provider_client.get_user_info(access_token)

    # Find or create user
    user = await find_or_create_user(
        provider=provider,
        provider_id=user_info.get("id") or "unknown",
        email=user_info.get("email"),
        name=user_info.get("name"),
        avatar_url=user_info.get("avatar_url"),
    )

    # Create JWT token
    jwt_token = create_user_token(user)

    return HTMLResponse(f"""
    <script>
        document.cookie = "access_token={jwt_token}; path=/; max-age={7*24*60*60}";
        window.location.href = "/";
    </script>
    """)


@router.get("/header-login", response_class=HTMLResponse)
async def header_login():
    """Redirect to trigger header-based authentication"""
    return HTMLResponse("""
    <script>
        window.location.href = "/";
    </script>
    """)
