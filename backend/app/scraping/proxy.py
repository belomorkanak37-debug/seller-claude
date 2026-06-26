"""Слой прокси: ротирующий шлюз или список с ротацией и cooldown.

Два режима (по конфигу):
- PROXY_URL — один endpoint резидентного провайдера, который сам меняет IP
  на каждый запрос (рекомендуемый, простейший). Всегда возвращается он же.
- PROXY_LIST — список прокси; ротация по кругу, временный бан (cooldown)
  для прокси, помеченных как «плохие» (бан/таймаут).

Если ни то ни другое не задано — режим без прокси (прямые запросы).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.config import settings


@dataclass
class ProxyPool:
    gateway: str = ""
    proxies: list[str] = field(default_factory=list)
    cooldown_seconds: float = 120.0

    _idx: int = 0
    _bad_until: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_settings(cls) -> "ProxyPool":
        return cls(
            gateway=settings.proxy_url,
            proxies=settings.proxy_list_items,
        )

    @property
    def enabled(self) -> bool:
        return bool(self.gateway or self.proxies)

    def get_proxy(self) -> str | None:
        """Возвращает строку прокси (http://...) или None для прямого запроса."""
        if self.gateway:
            return self.gateway
        if not self.proxies:
            return None

        now = time.monotonic()
        n = len(self.proxies)
        for _ in range(n):
            proxy = self.proxies[self._idx % n]
            self._idx += 1
            if self._bad_until.get(proxy, 0) <= now:
                return proxy
        # Все на cooldown — берём наименее «плохой», лучше попробовать, чем встать
        return min(self.proxies, key=lambda p: self._bad_until.get(p, 0))

    def mark_bad(self, proxy: str | None) -> None:
        """Помечает прокси из списка как временно недоступный."""
        if not proxy or proxy == self.gateway:
            return
        self._bad_until[proxy] = time.monotonic() + self.cooldown_seconds


# Глобальный пул (состояние ротации/cooldown общее на процесс)
proxy_pool = ProxyPool.from_settings()
