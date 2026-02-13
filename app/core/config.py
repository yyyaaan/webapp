from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Home Server"
    debug: bool = False

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    mongodb_uri: str
    mongodb_db_name: str = "home_server"

    github_client_id: str = ""
    github_client_secret: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""

    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""

    frontend_url: str = "http://localhost:8001"

    # Header-based authentication
    header_auth_enabled: bool = False
    databricks_header_auth: bool = False
    azure_app_service_auth: bool = False
    trusted_header_proxies: list[str] = ["127.0.0.1", "::1"]

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

@lru_cache
def get_settings() -> Settings:
    return Settings()
