"""Троттлинг запросов по хосту: минимальный интервал + случайная пауза.

Снижает частоту обращений к источнику, чтобы не получать баны. Состояние
(время последнего запроса по хосту) — на процесс. Для распределённого
троттлинга на нескольких воркерах можно вынести в Redis (задел на будущее).
"""

from __future__ import annotations

import asyncio
import random
import time
from urllib.parse import urlparse

from app.config import settings

_last_request: dict[str, float] = {}
_locks: dict[str, asyncio.Lock] = {}


def _host(url: str) -> str:
    return urlparse(url).netloc or url


def _lock_for(host: str) -> asyncio.Lock:
    lock = _locks.get(host)
    if lock is None:
        lock = asyncio.Lock()
        _locks[host] = lock
    return lock


async def throttle(url: str) -> None:
    """Ждёт, если с прошлого запроса к хосту прошло меньше интервала, плюс джиттер."""
    host = _host(url)
    min_interval = settings.throttle_min_interval
    jitter = settings.throttle_jitter

    async with _lock_for(host):
        now = time.monotonic()
        elapsed = now - _last_request.get(host, 0.0)
        wait = max(0.0, min_interval - elapsed)
        wait += random.uniform(0, jitter)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request[host] = time.monotonic()
