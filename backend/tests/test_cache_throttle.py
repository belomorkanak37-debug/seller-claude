import time

import pytest

from app.scraping import cache as cache_mod
from app.scraping import throttle as throttle_mod


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value


@pytest.mark.asyncio
async def test_cache_disabled_when_ttl_zero(monkeypatch):
    monkeypatch.setattr(cache_mod.settings, "provider_cache_ttl", 0)
    await cache_mod.cache_set("k", {"a": 1})
    assert await cache_mod.cache_get("k") is None


@pytest.mark.asyncio
async def test_cache_roundtrip_with_fake_redis(monkeypatch):
    monkeypatch.setattr(cache_mod.settings, "provider_cache_ttl", 60)
    fake = FakeRedis()
    monkeypatch.setattr(cache_mod, "_get_client", lambda: fake)
    await cache_mod.cache_set("wb:card:1", {"name": "Комод", "price": 100})
    got = await cache_mod.cache_get("wb:card:1")
    assert got == {"name": "Комод", "price": 100}


@pytest.mark.asyncio
async def test_throttle_enforces_min_interval(monkeypatch):
    monkeypatch.setattr(throttle_mod.settings, "throttle_min_interval", 0.1)
    monkeypatch.setattr(throttle_mod.settings, "throttle_jitter", 0.0)
    throttle_mod._last_request.clear()

    url = "https://throttle-test.example/path"
    await throttle_mod.throttle(url)  # первый — без ожидания
    start = time.monotonic()
    await throttle_mod.throttle(url)  # второй — должен подождать ~0.1с
    elapsed = time.monotonic() - start
    assert elapsed >= 0.08
