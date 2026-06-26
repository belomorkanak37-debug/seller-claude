"""Общий HTTP-слой для провайдеров: httpx-клиент с реалистичными заголовками,
таймаутами и экспоненциальными ретраями.

Полноценный слой устойчивости (ротация резидентных прокси, троттлинг,
решение капчи, Playwright-stealth) добавляется на Этапе 2. Здесь — лёгкая
база, которой достаточно для публичных JSON-эндпоинтов Wildberries.
"""

from __future__ import annotations

import asyncio
import logging
import random

import httpx

from app.scraping.proxy import proxy_pool
from app.scraping.throttle import throttle

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


class FetchError(Exception):
    """Не удалось получить ответ после всех ретраев."""


async def fetch_json(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: float = 10.0,
    retries: int = 3,
    backoff_base: float = 0.8,
    expected_status: tuple[int, ...] = (200,),
) -> dict | list:
    """GET с ретраями и backoff. Возвращает распарсенный JSON.

    Бросает FetchError, если все попытки не удались.
    """
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    last_exc: Exception | None = None
    proxy = proxy_pool.get_proxy()

    async with httpx.AsyncClient(
        timeout=timeout, follow_redirects=True, proxy=proxy
    ) as client:
        for attempt in range(1, retries + 1):
            try:
                # троттлинг по хосту: интервал + джиттер против банов
                await throttle(url)
                resp = await client.get(url, params=params, headers=merged_headers)
                if resp.status_code not in expected_status:
                    if resp.status_code in (403, 429):
                        proxy_pool.mark_bad(proxy)
                    raise FetchError(
                        f"{url} вернул статус {resp.status_code}"
                    )
                return resp.json()
            except (httpx.HTTPError, FetchError, ValueError) as exc:
                last_exc = exc
                if attempt < retries:
                    # экспоненциальный backoff + джиттер
                    delay = backoff_base * (2 ** (attempt - 1))
                    delay += random.uniform(0, 0.3)
                    logger.warning(
                        "fetch_json fail (%s/%s) %s: %s; retry in %.1fs",
                        attempt,
                        retries,
                        url,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)

    raise FetchError(f"Не удалось получить {url}: {last_exc}")
