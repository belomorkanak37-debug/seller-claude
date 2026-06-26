"""Фабрика провайдеров: по названию маркетплейса возвращает реализацию."""

from __future__ import annotations

from app.providers.base import Marketplace, MarketplaceProvider, ProviderError
from app.providers.stubs import OzonProvider, YandexMarketProvider
from app.providers.wildberries import WildberriesProvider

_REGISTRY: dict[Marketplace, type[MarketplaceProvider]] = {
    Marketplace.WILDBERRIES: WildberriesProvider,
    Marketplace.OZON: OzonProvider,
    Marketplace.YANDEX_MARKET: YandexMarketProvider,
}


class UnknownMarketplace(ProviderError):
    pass


def get_provider(marketplace: str) -> MarketplaceProvider:
    try:
        mp = Marketplace(marketplace)
    except ValueError as exc:
        raise UnknownMarketplace(
            f"Неизвестный маркетплейс: {marketplace!r}. "
            f"Доступно: {[m.value for m in Marketplace]}"
        ) from exc
    return _REGISTRY[mp]()
