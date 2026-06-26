"""Заглушки провайдеров Ozon и Яндекс Маркет.

Эти площадки защищены анти-ботом/капчей и требуют headless-браузера +
прокси — это реализуется на Этапе 2. Пока методы дают понятную ошибку,
а не молчаливую заглушку с фейковыми данными.
"""

from __future__ import annotations

from app.providers.base import (
    CompetitorDTO,
    Marketplace,
    MarketplaceProvider,
    ProductDTO,
    ReviewDTO,
    SourceUnavailable,
)

_MSG = (
    "Провайдер {mp} ещё не реализован — площадка требует headless-браузера и "
    "прокси (Этап 2). Пока доступен Wildberries."
)


class _NotImplementedProvider(MarketplaceProvider):
    def _fail(self):
        raise SourceUnavailable(_MSG.format(mp=self.marketplace.value))

    async def get_product(self, article: str) -> ProductDTO:
        self._fail()

    async def search_competitors(
        self, keywords: list[str], limit: int = 10
    ) -> list[CompetitorDTO]:
        self._fail()

    async def get_reviews(self, product_id: str, limit: int = 50) -> list[ReviewDTO]:
        self._fail()

    async def get_price(self, product_id: str) -> float | None:
        self._fail()

    async def get_tags(self, product_id: str) -> list[str]:
        self._fail()

    async def get_stock(self, product_id: str) -> int | None:
        self._fail()


class OzonProvider(_NotImplementedProvider):
    marketplace = Marketplace.OZON


class YandexMarketProvider(_NotImplementedProvider):
    marketplace = Marketplace.YANDEX_MARKET
