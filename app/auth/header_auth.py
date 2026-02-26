from fastapi import Request
from typing import Optional, Dict, Any
import json
import base64
import binascii

from app.core.config import get_settings
from app.auth.user_service import find_or_create_user, create_user_token

settings = get_settings()


class HeaderAuthProvider:
    """Base class for header-based authentication providers"""

    def extract_user_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract user information from request headers"""
        raise NotImplementedError

    def validate_request(self, request: Request) -> bool:
        """Validate that the request is from a trusted source"""
        if not request.client:
            return False
        client_ip = request.client.host
        return client_ip in settings.trusted_header_proxies


class DatabricksAuthProvider(HeaderAuthProvider):
    """Databricks App mode authentication provider"""

    def extract_user_info(self, request: Request) -> Optional[Dict[str, Any]]:
        if not self.validate_request(request):
            return None

        # Databricks provides user info in specific headers
        email = request.headers.get("X-Databricks-User-Email")
        name = request.headers.get("X-Databricks-User-Name") or email.split("@")[0] if email else None

        if not email:
            return None

        return {
            "email": email,
            "name": name,
            "provider": "databricks",
            "provider_id": email,
            "avatar_url": None
        }


class AzureAppServiceProvider(HeaderAuthProvider):
    """Azure App Service authentication provider"""

    def extract_user_info(self, request: Request) -> Optional[Dict[str, Any]]:
        if not self.validate_request(request):
            return None

        # Azure App Service provides user info in X-MS-CLIENT-PRINCIPAL header
        principal_header = request.headers.get("X-MS-CLIENT-PRINCIPAL")
        if not principal_header:
            return None

        try:
            # Decode the base64 encoded principal data
            principal_data = json.loads(base64.b64decode(principal_header).decode())

            return {
                "email": principal_data.get("userDetails", ""),
                "name": principal_data.get("userDetails", "").split("@")[0] if principal_data.get("userDetails") else None,
                "provider": "azure_app_service",
                "provider_id": principal_data.get("userId", ""),
                "avatar_url": None
            }
        except (json.JSONDecodeError, binascii.Error, UnicodeDecodeError):
            return None


class HeaderAuthManager:
    """Manages header-based authentication across different providers"""

    def __init__(self):
        self.providers = {
            "databricks": DatabricksAuthProvider(),
            "azure_app_service": AzureAppServiceProvider()
        }

    async def authenticate_from_headers(self, request: Request) -> Optional[str]:
        """Authenticate user from headers and return JWT token"""
        if not settings.header_auth_enabled:
            return None

        # Try each enabled provider
        if settings.databricks_header_auth:
            user_info = self.providers["databricks"].extract_user_info(request)
            if user_info:
                return await self._create_or_get_user(user_info)

        if settings.azure_app_service_auth:
            user_info = self.providers["azure_app_service"].extract_user_info(request)
            if user_info:
                return await self._create_or_get_user(user_info)

        return None

    async def _create_or_get_user(self, user_info: Dict[str, Any]) -> str:
        """Create user or get existing user and return JWT token"""
        # Find or create user using shared service
        user = await find_or_create_user(
            provider=user_info["provider"],
            provider_id=user_info["provider_id"],
            email=user_info["email"],
            name=user_info["name"],
            avatar_url=user_info.get("avatar_url"),
        )

        # Create JWT token
        return create_user_token(user)


# Global instance
header_auth_manager = HeaderAuthManager()
