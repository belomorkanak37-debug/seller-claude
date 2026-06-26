"""Провайдер Ozon.

Ozon защищён анти-ботом, поэтому карточку рендерим в headless-браузере и
парсим из перехваченного composer-api JSON (основной источник) с fallback на
ld+json. Картинка/цена/рейтинг/теги — из widgetStates.
"""

from __future__ import annotations

import logging

from app.providers.base import (
    CompetitorDTO,
    Marketplace,
    MarketplaceProvider,
    ProductDTO,
    ProductNotFound,
    ReviewDTO,
    SourceUnavailable,
)
import re

from app.scraping.browser import render
from app.scraping.cache import cache_get, cache_set
from app.scraping.parsers import (
    parse_ldjson_itemlist,
    parse_ldjson_product,
    parse_ozon_composer,
)

logger = logging.getLogger(__name__)


def _article_from_url(url: str | None) -> str | None:
    if not url:
        return None
    matches = re.findall(r"(\d{5,})", url)
    return matches[-1] if matches else None


class OzonProvider(MarketplaceProvider):
    marketplace = Marketplace.OZON

    def _product_url(self, article: str) -> str:
        return f"https://www.ozon.ru/product/{article}/"

    async def get_product(self, article: str) -> ProductDTO:
        cache_key = f"ozon:product:{article}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return _dto_from_dict(cached)

        url = self._product_url(article)
        result = await render(
            url,
            capture_json_substrings=["composer-api.bx/page/json"],
        )

        parsed: dict = {}
        # 1) Основной источник — composer-api
        for body in result.json_responses.values():
            data = parse_ozon_composer(body)
            if data.get("name"):
                parsed = data
                break
        # 2) Fallback — ld+json со страницы
        if not parsed.get("name"):
            parsed = parse_ldjson_product(result.html)

        if not parsed.get("name"):
            raise ProductNotFound(f"Не удалось разобрать карточку Ozon {article}")

        dto = ProductDTO(
            marketplace=self.marketplace,
            article=str(article),
            name=parsed.get("name") or "Без названия",
            price=parsed.get("price"),
            photo_url=parsed.get("photo_url"),
            rating=parsed.get("rating"),
            reviews_count=parsed.get("reviews_count"),
            tags=parsed.get("tags") or [],
            stock=None,
            url=url,
            root_id=str(article),
            brand=parsed.get("brand"),
        )
        await cache_set(cache_key, _dto_to_dict(dto))
        return dto

    async def get_reviews(self, product_id: str, limit: int = 50) -> list[ReviewDTO]:
        # Полноценный сбор отзывов Ozon — на Этапе 4; здесь best-effort пусто.
        return []

    async def search_competitors(
        self, keywords: list[str], limit: int = 10
    ) -> list[CompetitorDTO]:
        query = " ".join(keywords).strip()
        if not query:
            return []
        url = f"https://www.ozon.ru/search/?text={query.replace(' ', '+')}"
        result = await render(url)
        items = parse_ldjson_itemlist(result.html)
        competitors: list[CompetitorDTO] = []
        for it in items[:limit]:
            if not it.get("name"):
                continue
            competitors.append(
                CompetitorDTO(
                    marketplace=self.marketplace,
                    article=_article_from_url(it.get("url")),
                    name=it["name"],
                    price=it.get("price"),
                    photo_url=it.get("photo_url"),
                    rating=it.get("rating"),
                    reviews_count=it.get("reviews_count"),
                    url=it.get("url"),
                )
            )
        if not competitors:
            raise SourceUnavailable(
                "Не удалось получить результаты поиска Ozon (нужны прокси/решатель капчи)"
            )
        return competitors

    async def get_price(self, product_id: str) -> float | None:
        return (await self.get_product(product_id)).price

    async def get_tags(self, product_id: str) -> list[str]:
        return (await self.get_product(product_id)).tags

    async def get_stock(self, product_id: str) -> int | None:
        return (await self.get_product(product_id)).stock


def _dto_to_dict(dto: ProductDTO) -> dict:
    return {
        "article": dto.article,
        "name": dto.name,
        "price": dto.price,
        "photo_url": dto.photo_url,
        "rating": dto.rating,
        "reviews_count": dto.reviews_count,
        "tags": dto.tags,
        "stock": dto.stock,
        "url": dto.url,
        "root_id": dto.root_id,
        "brand": dto.brand,
    }


def _dto_from_dict(d: dict) -> ProductDTO:
    return ProductDTO(
        marketplace=Marketplace.OZON,
        article=d["article"],
        name=d["name"],
        price=d.get("price"),
        photo_url=d.get("photo_url"),
        rating=d.get("rating"),
        reviews_count=d.get("reviews_count"),
        tags=d.get("tags") or [],
        stock=d.get("stock"),
        url=d.get("url"),
        root_id=d.get("root_id"),
        brand=d.get("brand"),
    )
