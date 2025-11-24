from fastapi import APIRouter, Request, responses, status
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from pymongo import ReturnDocument
from datetime import datetime, timezone

from app.core.config import settings
from app.core.db import user_collection

router = APIRouter()

oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

oauth.register(
    name='microsoft',
    client_id=settings.MICROSOFT_CLIENT_ID,
    client_secret=settings.MICROSOFT_CLIENT_SECRET,
    server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
    client_kwargs={'scope': 'User.Read'}
)

oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'read:user user:email'}
)


def normalize_user_profile(provider: str, user_info: dict) -> dict:
    """Creates a standard user profile from different SSO provider data."""
    if provider == 'google':
        return {
            'name': user_info.get('name'),
            'email': user_info.get('email'),
            'picture': user_info.get('picture')
        }
    elif provider == 'microsoft':
        return {
            'name': user_info.get('displayName'),
            'email': user_info.get('userPrincipalName'),
            'picture': None
        }
    elif provider == 'github':
        return {
            'name': user_info.get('name') or user_info.get('login'),
            'email': user_info.get('email'),
            'picture': user_info.get('avatar_url')
        }
    return {}


@router.get('/login/{provider}')
async def login(request: Request, provider: str):
    """Redirects the user to the provider's authentication page."""
    try:
        redirect_uri = f"{settings.REDIRECT_BASE_URL}/auth/{provider}/callback"
        return await getattr(oauth, provider).authorize_redirect(request, redirect_uri)
    except Exception:
        return RedirectResponse(url=f"/?error=provider_unreachable&message=Network error with {provider}; the cloud provider may block the connection. Try Github login.")


def serialize_user_document(doc: dict) -> dict:
    if doc.get("_id"):
        doc["_id"] = str(doc["_id"])
    if doc.get("created_at"):
        doc["created_at"] = doc["created_at"].isoformat()
    if doc.get("last_login_at"):
        doc["last_login_at"] = doc["last_login_at"].isoformat()
    return doc


@router.get('/{provider}/callback')
async def auth_callback(request: Request, provider: str):
    # ... (the first part of the function fetching user_info is unchanged) ...
    try:
        token = await getattr(oauth, provider).authorize_access_token(request)
        if provider == 'github':
            resp = await oauth.github.get('user', token=token)
            user_info = resp.json()
        else:
            user_info = token.get('userinfo')
    except Exception:
        return RedirectResponse(url="/?error=auth_failed")

    if not user_info:
        return RedirectResponse(url="/?error=user_info_failed")

    normalized_profile = normalize_user_profile(provider, user_info)
    user_email = normalized_profile.get("email")

    user_from_db = await user_collection.find_one_and_update(
        {"email": user_email},
        {
            "$set": {
                "name": normalized_profile.get("name"),
                "picture": normalized_profile.get("picture"),
                "last_login_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "email": user_email,
                "role": "user",
                "created_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    serializable_user = serialize_user_document(user_from_db)
    request.session['user'] = serializable_user
    return RedirectResponse(url="/dashboard")


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    response = responses.Response(status_code=status.HTTP_200_OK)
    response.headers["HX-Redirect"] = "/"
    return response
