from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OAuthProviderConfig:
    client_id: str
    client_secret: str
    authorize_url: str
    access_token_url: str
    user_info_url: str
    scope: str


class OAuthProvider(ABC):
    def __init__(self, config: OAuthProviderConfig):
        self.config = config

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        pass

    @abstractmethod
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> dict:
        pass


class OAuthProviderRegistry:
    def __init__(self):
        self._providers: dict[str, OAuthProvider] = {}

    def register(self, name: str, provider: OAuthProvider):
        self._providers[name] = provider

    def get(self, name: str) -> OAuthProvider | None:
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())


registry = OAuthProviderRegistry()
