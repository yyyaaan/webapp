from os import environ
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_DETAILS: str
    SESSION_SECRET_KEY: str

    MEM_DISK_PATH: str = "/tmp/cache"

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str

    REDIRECT_BASE_URL: str = "http://localhost:8001"

    # all DBX settings optional, and automatic if run on DBX
    DATABRICKS_APP_NAME: str = "N/A"
    DATABRICKS_APP_URL: str = "N/A"
    DATABRICKS_HOST: str = "N/A"
    DATABRICKS_CLIENT_ID: str = "N/A"
    DATABRICKS_CLIENT_SECRET: str = "N/A"
    DATABRICKS_WORKSPACE_ID: str = "N/A"

    def get_redacted_dict(self, include_os: bool = False) -> dict:
        redacted = self.model_dump()
        if include_os:
            redacted.update({f"_OS_{k}": v for k, v in environ.items()})
        for key in redacted.keys():
            if "SECRET" in key or "KEY" in key or "CLIENT" in key or "PASSWORD" in key:
                if len(redacted[key]) > 3:
                   redacted[key] = redacted[key][0] + "********" + redacted[key][-1]
            if "MONGO_DETAILS" in key:
                redacted[key] = redacted[key][:25] + "..." + redacted[key][-10:]

        return redacted  # dict(sorted(redacted.items()))
        

    class Config:
        env_file = ".env"


settings = Settings()
