"""Абстракция «провайдер данных маркетплейса».

Единый интерфейс, за которым скрыт способ получения данных (публичный
эндпоинт или парсинг). Бизнес-логика работает только с этим интерфейсом,
поэтому источник можно менять, не трогая остальной код.

Конкретные реализации (OzonProvider, WildberriesProvider,
YandexMarketProvider) появятся на Этапе 2. Здесь — только контракт и
доменные DTO, чтобы Этап 1 опирался на стабильный интерфейс.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Marketplace(str, Enum):
    OZON = "ozon"
    WILDBERRIES = "wildberries"
    YANDEX_MARKET = "yandex_market"


class ProviderError(Exception):
    """Базовая ошибка провайдера."""


class ProductNotFound(ProviderError):
    """Товар по артикулу не найден."""


class CaptchaRequired(ProviderError):
    """Источник запросил капчу."""


class SourceUnavailable(ProviderError):
    """Источник недоступен (бан прокси, таймаут, смена вёрстки)."""


@dataclass
class ReviewDTO:
    external_id: str | None
    author: str | None
    text: str | None
    rating: float | None
    published_at: datetime | None
    source: str


@dataclass
class ProductDTO:
    marketplace: Marketplace
    article: str
    name: str
    price: float | None = None
    photo_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    tags: list[str] = field(default_factory=list)
    stock: int | None = None
    url: str | None = None


@dataclass
class CompetitorDTO:
    marketplace: Marketplace
    article: str | None
    name: str
    price: float | None = None
    photo_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    url: str | None = None


class MarketplaceProvider(abc.ABC):
    """Контракт провайдера. Все методы — async (за ними сеть/парсинг)."""

    marketplace: Marketplace

    @abc.abstractmethod
    async def get_product(self, article: str) -> ProductDTO:
        ...

    @abc.abstractmethod
    async def search_competitors(
        self, keywords: list[str], limit: int = 10
    ) -> list[CompetitorDTO]:
        ...

    @abc.abstractmethod
    async def get_reviews(self, product_id: str, limit: int = 50) -> list[ReviewDTO]:
        ...

    @abc.abstractmethod
    async def get_price(self, product_id: str) -> float | None:
        ...

    @abc.abstractmethod
    async def get_tags(self, product_id: str) -> list[str]:
        ...

    @abc.abstractmethod
    async def get_stock(self, product_id: str) -> int | None:
        ...
