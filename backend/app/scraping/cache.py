"""Кеш результатов парсинга в Redis с TTL.

Чтобы не дёргать площадку на каждый запрос пользователя, результаты
провайдеров кладём в Redis на provider_cache_ttl секунд. Если Redis
недоступен или TTL=0 — кеш прозрачно отключается (работаем напрямую).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def _get_client() -> redis.Redis | None:
    global _client
    if settings.provider_cache_ttl <= 0:
        return None
    if _client is None:
        try:
            _client = redis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis-кеш недоступен: %s", exc)
            return None
    return _client


async def cache_get(key: str) -> Any | None:
    client = _get_client()
    if client is None:
        return None
    try:
        raw = await client.get(key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache_get fail %s: %s", key, exc)
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    client = _get_client()
    if client is None:
        return
    ttl = settings.provider_cache_ttl if ttl is None else ttl
    if ttl <= 0:
        return
    try:
        await client.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache_set fail %s: %s", key, exc)
