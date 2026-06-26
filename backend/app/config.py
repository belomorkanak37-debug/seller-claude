from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения. Значения читаются из переменных окружения (.env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://seller:changeme@db:5432/seller"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Telegram
    bot_token: str = ""
    webapp_url: str = ""

    # App
    secret_key: str = "change_me"
    cors_origins: str = ""
    # Максимальный возраст initData в секундах (0 = не проверять).
    initdata_max_age_seconds: int = 86400

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_origins:
            return []
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
