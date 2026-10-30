"""Application settings, read from environment variables (SEC-05: no secrets in code)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ReqTrace"
    database_url: str = "sqlite:///./reqtrace.db"
    jwt_secret: str = "change-me-in-env"
    session_minutes: int = 60
    max_upload_mb: int = 10
    storage_dir: str = "./storage"

    # Initial Administrator account, created at start-up if both are set
    admin_email: str = ""
    admin_password: str = ""

    # LLM provider: "gemini" in deployment, "mock" for tests and offline demos
    llm_provider: str = "mock"
    gemini_api_key: str = ""
    # Comma-separated: the first model is used, the others are fallbacks when it is busy or retired
    gemini_model: str = "gemini-3-flash-preview,gemini-3.1-flash-lite"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
