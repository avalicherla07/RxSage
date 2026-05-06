from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    supabase_url: str
    supabase_service_key: str
    admin_key: str
    port: int = 8000
    pubmed_enabled: bool = True
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance. Call get_settings.cache_clear() in tests."""
    return Settings()
