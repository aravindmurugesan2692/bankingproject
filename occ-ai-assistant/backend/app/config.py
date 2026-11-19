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

    # LLM (Phase 2) — used only when MOCK_MODE=false and a key is present
    openai_api_key: str = ""
    llm_provider: str = "openai"  # openai | compatible
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_seconds: float = 45.0

    # ServiceNow (Phase 3) — live only when MOCK_MODE=false and instance+auth configured
    servicenow_instance_url: str = ""
    servicenow_username: str = ""
    servicenow_password: str = ""
    servicenow_client_id: str = ""
    servicenow_client_secret: str = ""
    servicenow_timeout_seconds: float = 30.0
    servicenow_max_retries: int = 2

    # Later phases
    pagerduty_api_token: str = ""
    microsoft_tenant_id: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def use_live_llm(self) -> bool:
        return (not self.mock_mode) and bool(self.openai_api_key.strip())

    @property
    def servicenow_configured(self) -> bool:
        return bool(
            self.servicenow_instance_url.strip()
            and (
                (self.servicenow_username.strip() and self.servicenow_password.strip())
                or (
                    self.servicenow_client_id.strip()
                    and self.servicenow_client_secret.strip()
                )
            )
        )

    @property
    def use_live_servicenow(self) -> bool:
        return (not self.mock_mode) and self.servicenow_configured


@lru_cache
def get_settings() -> Settings:
    return Settings()
