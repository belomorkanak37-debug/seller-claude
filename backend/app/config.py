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

    # ── Слой парсинга (Этап 2) ────────────────────────────────
    # Прокси: ротирующий шлюз (один endpoint, сам меняет IP) ИЛИ список.
    proxy_url: str = ""           # http://user:pass@gateway:port
    proxy_list: str = ""          # через запятую: http://u:p@host:port, ...
    # Капча: провайдер и ключ (2captcha/rucaptcha-совместимый протокол).
    captcha_provider: str = "twocaptcha"   # twocaptcha | none
    captcha_api_key: str = ""
    captcha_base_url: str = "https://2captcha.com"  # rucaptcha: https://rucaptcha.com
    # Кеш результатов парсинга в Redis (сек). 0 = не кешировать.
    provider_cache_ttl: int = 3600
    # Троттлинг: минимальный интервал между запросами к одному хосту (сек)
    # и верхняя граница случайной паузы (джиттер).
    throttle_min_interval: float = 1.5
    throttle_jitter: float = 1.0
    # Playwright
    playwright_headless: bool = True
    playwright_nav_timeout_ms: int = 45000

    # ── AI (Этап 10) ──────────────────────────────────────────
    # Провайдер LLM: claude | none. Слой абстрактный, дефолт — Claude.
    llm_provider: str = "claude"
    anthropic_api_key: str = ""
    llm_model: str = "claude-opus-4-8"
    llm_max_tokens: int = 2048

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_origins:
            return []
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def proxy_list_items(self) -> list[str]:
        if not self.proxy_list:
            return []
        return [p.strip() for p in self.proxy_list.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
