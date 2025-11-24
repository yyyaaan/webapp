from fastapi import Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from logging import getLogger

from ..core.db import api_key_collection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v3/token", auto_error=False)
logger = getLogger("core.auth")


def get_current_user(request: Request) -> dict | None:
    return request.session.get("user")


def require_user(request: Request) -> dict:
    logger.info("Requiring authenticated user from session")
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_admin_user(user: dict = Depends(require_user)) -> dict:
    logger.info(f"Checking admin privileges for user: {user}")
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    return user


async def require_api_key(token: str = Depends(oauth2_scheme)) -> dict:
    logger.info(f"Validating API Key: {str(token)[:5]}***")
    api_key_data = await api_key_collection.find_one({"key": token, "is_active": True})

    if api_key_data:
        return {
            "email": api_key_data["owner_email"],
            "type": "api_key"
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or inactive API Key",
    )


async def require_user_or_api_key(request: Request, token: str | None = Depends(oauth2_scheme)):
    """
    Dependency that requires either a valid session user or a valid API key.
    It first checks for a user in the session. If not found, it then
    validates the API key provided in the Authorization header.
    """
    logger.info(f"Authenticating user session, databricks or API key.")

    user = request.session.get("user")
    if user:
        logger.info(f"Authenticated via session: {user.get('email', '=unknown=')}")
        return user

    dbx_email = request.headers.get("X-Databricks-Email")
    if dbx_email:
        logger.info(f"Authenticated via Databricks: {dbx_email}")
        return {"email": dbx_email, "name": dbx_email.split('@')[0], "role": "user", "type": "databricks"}

    if token:
        logger.info(f"Validating API Key after session checked: {token[:5]}***")
        api_key_data = await api_key_collection.find_one({"key": token, "is_active": True})
        if api_key_data:
            return {
                "email": api_key_data["owner_email"],
                "type": "api_key"
            }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. A valid user session or API key is required.",
    )
