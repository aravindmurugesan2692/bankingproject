"""Environment-based configuration. Secrets never hardcoded."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "OCC AI Assistant"
    mock_mode: bool = True
    database_url: str = "sqlite:///./occ_ai_assistant.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    api_prefix: str = "/api"

    # Placeholders for later phases — never hardcode real secrets
    openai_api_key: str = ""
    servicenow_instance_url: str = ""
    servicenow_username: str = ""
    servicenow_password: str = ""
    pagerduty_api_token: str = ""
    microsoft_tenant_id: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
