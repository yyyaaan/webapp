import httpx
from app.auth.providers import OAuthProvider, OAuthProviderConfig


class GoogleOAuthProvider(OAuthProvider):
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "scope": self.config.scope,
            "response_type": "code",
            "state": state,
        }
        url = f"{self.config.authorize_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return url

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.access_token_url,
                data={
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.config.user_info_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            user_data = response.json()

            return {
                "id": user_data.get("sub") or user_data.get("email"),
                "email": user_data.get("email"),
                "name": user_data.get("name") or "User",
                "avatar_url": user_data.get("picture"),
            }
