"""Headless-браузер (Playwright) со stealth-настройками и прокси.

Используется провайдерами защищённых площадок (Ozon, Яндекс Маркет). Импорт
Playwright ленивый — модуль можно импортировать без установленного браузера
(нужно для юнит-тестов парсеров, которые браузер не запускают).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from app.config import settings
from app.providers.base import SourceUnavailable
from app.scraping.proxy import proxy_pool

logger = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Скрипт маскировки автоматизации (минимальный stealth).
_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU','ru','en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
window.chrome = { runtime: {} };
"""


@dataclass
class RenderResult:
    url: str
    status: int | None
    html: str
    json_responses: dict[str, dict]


def _proxy_kwargs() -> dict:
    proxy = proxy_pool.get_proxy()
    if not proxy:
        return {}
    # Playwright принимает proxy={"server": "...", "username":..., "password":...}
    from urllib.parse import urlparse

    parsed = urlparse(proxy)
    server = f"{parsed.scheme}://{parsed.hostname}"
    if parsed.port:
        server += f":{parsed.port}"
    cfg: dict = {"server": server}
    if parsed.username:
        cfg["username"] = parsed.username
    if parsed.password:
        cfg["password"] = parsed.password
    return {"proxy": cfg}


async def render(
    url: str,
    *,
    capture_json_substrings: Iterable[str] = (),
    wait_until: str = "domcontentloaded",
    captcha_markers: Iterable[str] = ("g-recaptcha", "captcha", "Доступ ограничен"),
) -> RenderResult:
    """Открывает страницу в headless-Chromium и возвращает HTML + перехваченные JSON.

    capture_json_substrings — подстроки URL, JSON-ответы которых нужно собрать
    (например, composer-api у Ozon). Бросает SourceUnavailable/CaptchaRequired.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:  # pragma: no cover
        raise SourceUnavailable(
            "Playwright не установлен — провайдер недоступен"
        ) from exc

    from app.providers.base import CaptchaRequired

    substrings = list(capture_json_substrings)
    captured: dict[str, dict] = {}
    proxy = proxy_pool.get_proxy()

    async with async_playwright() as pw:
        try:
            browser = await pw.chromium.launch(
                headless=settings.playwright_headless,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
        except Exception as exc:  # noqa: BLE001
            raise SourceUnavailable(f"Не удалось запустить браузер: {exc}") from exc

        try:
            context = await browser.new_context(
                user_agent=_UA,
                locale="ru-RU",
                timezone_id="Europe/Moscow",
                viewport={"width": 1366, "height": 768},
                extra_http_headers={"Accept-Language": "ru-RU,ru;q=0.9"},
                **_proxy_kwargs(),
            )
            await context.add_init_script(_STEALTH_JS)
            page = await context.new_page()

            async def on_response(resp):
                if substrings and any(s in resp.url for s in substrings):
                    try:
                        captured[resp.url] = await resp.json()
                    except Exception:  # noqa: BLE001
                        pass

            page.on("response", on_response)

            try:
                response = await page.goto(
                    url,
                    wait_until=wait_until,
                    timeout=settings.playwright_nav_timeout_ms,
                )
            except Exception as exc:  # noqa: BLE001
                proxy_pool.mark_bad(proxy)
                raise SourceUnavailable(f"Навигация не удалась: {exc}") from exc

            html = await page.content()
            status = response.status if response else None

            lowered = html.lower()
            if status in (403, 429) or any(
                m.lower() in lowered for m in captcha_markers
            ):
                raise CaptchaRequired(
                    "Источник показал капчу/блокировку. Требуется решатель капчи и/или прокси."
                )

            return RenderResult(
                url=url, status=status, html=html, json_responses=captured
            )
        finally:
            await browser.close()
