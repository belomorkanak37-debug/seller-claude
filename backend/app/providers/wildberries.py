"""Провайдер Wildberries.

Источник — публичные JSON-эндпоинты WB (карточка, цена, остатки, отзывы,
характеристики). Headless-браузер не нужен. Всё, что специфично для WB
(хосты basket, формула картинки, копейки в цене), инкапсулировано здесь —
бизнес-логика про это не знает.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.providers.base import (
    CompetitorDTO,
    Marketplace,
    MarketplaceProvider,
    ProductDTO,
    ProductNotFound,
    ReviewDTO,
    SourceUnavailable,
)
from app.providers.http import FetchError, fetch_json
from app.scraping.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

# dest — регион доставки. Без валидного dest WB не отдаёт цену/остатки.
# -1257786 — общий публичный идентификатор (Москва/центр).
_DEST = "-1257786"
_CARD_DETAIL_URL = "https://card.wb.ru/cards/v2/detail"
_SEARCH_URL = "https://search.wb.ru/exactmatch/ru/common/v5/search"
# Хосты для отзывов (часть товаров на feedbacks1, часть на feedbacks2).
_FEEDBACK_HOSTS = ["https://feedbacks2.wb.ru", "https://feedbacks1.wb.ru"]


def _basket_host(vol: int) -> str:
    """Определяет номер basket-хоста по vol (= nm // 100000).

    Диапазоны WB периодически смещаются; таблица актуальна на момент
    написания, при промахе картинка просто не отрисуется — некритично.
    """
    ranges = [
        (143, "01"), (287, "02"), (431, "03"), (719, "04"), (1007, "05"),
        (1061, "06"), (1115, "07"), (1169, "08"), (1313, "09"), (1601, "10"),
        (1655, "11"), (1919, "12"), (2045, "13"), (2189, "14"), (2405, "15"),
        (2621, "16"), (2837, "17"), (3053, "18"), (3269, "19"), (3485, "20"),
        (3701, "21"), (3917, "22"), (4133, "23"), (4349, "24"), (4565, "25"),
    ]
    for upper, host in ranges:
        if vol <= upper:
            return host
    return "26"


def wb_image_url(nm: int) -> str:
    vol = nm // 100000
    part = nm // 1000
    host = _basket_host(vol)
    return (
        f"https://basket-{host}.wbbasket.ru/vol{vol}/part{part}/{nm}"
        f"/images/big/1.webp"
    )


def _card_json_url(nm: int) -> str:
    vol = nm // 100000
    part = nm // 1000
    host = _basket_host(vol)
    return (
        f"https://basket-{host}.wbbasket.ru/vol{vol}/part{part}/{nm}"
        f"/info/ru/card.json"
    )


def _kopecks_to_rub(value) -> float | None:
    try:
        return round(int(value) / 100, 2)
    except (TypeError, ValueError):
        return None


def _extract_price(product: dict) -> float | None:
    # v2: цена в sizes[].price.{basic,product,total} в копейках
    for size in product.get("sizes", []) or []:
        price = size.get("price") or {}
        for key in ("product", "total", "basic"):
            if price.get(key):
                rub = _kopecks_to_rub(price[key])
                if rub:
                    return rub
    # fallback на старые поля
    for key in ("salePriceU", "priceU"):
        if product.get(key):
            rub = _kopecks_to_rub(product[key])
            if rub:
                return rub
    return None


def _extract_stock(product: dict) -> int | None:
    total = 0
    found = False
    for size in product.get("sizes", []) or []:
        for stock in size.get("stocks", []) or []:
            qty = stock.get("qty")
            if isinstance(qty, int):
                total += qty
                found = True
    return total if found else None


def _extract_rating(product: dict) -> float | None:
    for key in ("reviewRating", "rating", "supplierRating"):
        val = product.get(key)
        if isinstance(val, (int, float)) and val:
            # rating иногда приходит как 1-5, reviewRating как 4.7 — оба ок
            return round(float(val), 2)
    return None


class WildberriesProvider(MarketplaceProvider):
    marketplace = Marketplace.WILDBERRIES

    async def _fetch_card(self, article: str) -> dict:
        try:
            nm = int(article)
        except ValueError as exc:
            raise ProductNotFound(
                f"Артикул WB должен быть числом, получено: {article!r}"
            ) from exc

        cache_key = f"wb:card:{nm}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            data = await fetch_json(
                _CARD_DETAIL_URL,
                params={
                    "appType": 1,
                    "curr": "rub",
                    "dest": _DEST,
                    "spp": 30,
                    "nm": nm,
                },
            )
        except FetchError as exc:
            raise SourceUnavailable(f"WB недоступен: {exc}") from exc

        products = (data or {}).get("data", {}).get("products", [])
        if not products:
            raise ProductNotFound(f"Товар WB {article} не найден")
        await cache_set(cache_key, products[0])
        return products[0]

    async def get_product(self, article: str) -> ProductDTO:
        product = await self._fetch_card(article)
        nm = int(product.get("id", article))

        tags = await self._fetch_tags(nm)

        return ProductDTO(
            marketplace=self.marketplace,
            article=str(nm),
            name=product.get("name") or "Без названия",
            price=_extract_price(product),
            photo_url=wb_image_url(nm),
            rating=_extract_rating(product),
            reviews_count=product.get("feedbacks"),
            tags=tags,
            stock=_extract_stock(product),
            url=f"https://www.wildberries.ru/catalog/{nm}/detail.aspx",
            root_id=str(product.get("root")) if product.get("root") else None,
            brand=product.get("brand"),
        )

    async def _fetch_tags(self, nm: int) -> list[str]:
        """Характеристики товара из basket card.json (реальные теги)."""
        cache_key = f"wb:tags:{nm}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            data = await fetch_json(_card_json_url(nm), retries=2)
        except FetchError:
            return []
        if not isinstance(data, dict):
            return []
        tags: list[str] = []
        # options: [{"name": ..., "value": ...}]
        for opt in data.get("options", []) or []:
            name = opt.get("name")
            value = opt.get("value")
            if name and value:
                tags.append(f"{name}: {value}")
        # grouped_options для более новой структуры
        for group in data.get("grouped_options", []) or []:
            for opt in group.get("options", []) or []:
                name = opt.get("name")
                value = opt.get("value")
                if name and value:
                    pair = f"{name}: {value}"
                    if pair not in tags:
                        tags.append(pair)
        tags = tags[:40]
        await cache_set(cache_key, tags)
        return tags

    async def get_reviews(self, product_id: str, limit: int = 50) -> list[ReviewDTO]:
        """Отзывы по imtId (root). Пробуем оба feedback-хоста."""
        for host in _FEEDBACK_HOSTS:
            try:
                data = await fetch_json(
                    f"{host}/feedbacks/v1/{product_id}", retries=2
                )
            except FetchError:
                continue
            if not isinstance(data, dict):
                continue
            feedbacks = data.get("feedbacks")
            if not feedbacks:
                # Этот хост вернул пусто — пробуем следующий
                continue
            return self._parse_feedbacks(feedbacks, limit)
        return []

    @staticmethod
    def _parse_feedbacks(feedbacks: list, limit: int) -> list[ReviewDTO]:
        result: list[ReviewDTO] = []
        for fb in feedbacks[:limit]:
            text = (fb.get("text") or "").strip()
            pros = (fb.get("pros") or "").strip()
            cons = (fb.get("cons") or "").strip()
            parts = [p for p in (text, pros and f"+ {pros}", cons and f"- {cons}") if p]
            full_text = "\n".join(parts) if parts else None

            published = None
            raw_date = fb.get("createdDate") or fb.get("date")
            if raw_date:
                try:
                    published = datetime.fromisoformat(
                        str(raw_date).replace("Z", "+00:00")
                    ).astimezone(timezone.utc).replace(tzinfo=None)
                except ValueError:
                    published = None

            author = None
            details = fb.get("wbUserDetails") or {}
            author = details.get("name") or fb.get("userName")

            result.append(
                ReviewDTO(
                    external_id=str(fb.get("id")) if fb.get("id") else None,
                    author=author,
                    text=full_text,
                    rating=fb.get("productValuation"),
                    published_at=published,
                    source=Marketplace.WILDBERRIES.value,
                )
            )
        return result

    async def search_competitors(
        self, keywords: list[str], limit: int = 10
    ) -> list[CompetitorDTO]:
        """Поиск конкурентов по ключевым словам (используется на Этапе 3)."""
        query = " ".join(keywords).strip()
        if not query:
            return []
        try:
            data = await fetch_json(
                _SEARCH_URL,
                params={
                    "appType": 1,
                    "curr": "rub",
                    "dest": _DEST,
                    "query": query,
                    "resultset": "catalog",
                    "sort": "popular",
                    "spp": 30,
                    "limit": limit,
                },
            )
        except FetchError as exc:
            raise SourceUnavailable(f"WB поиск недоступен: {exc}") from exc

        products = (data or {}).get("data", {}).get("products", [])[:limit]
        result: list[CompetitorDTO] = []
        for p in products:
            nm = p.get("id")
            if not nm:
                continue
            result.append(
                CompetitorDTO(
                    marketplace=self.marketplace,
                    article=str(nm),
                    name=p.get("name") or "Без названия",
                    price=_extract_price(p),
                    photo_url=wb_image_url(int(nm)),
                    rating=_extract_rating(p),
                    reviews_count=p.get("feedbacks"),
                    url=f"https://www.wildberries.ru/catalog/{nm}/detail.aspx",
                )
            )
        return result

    async def get_price(self, product_id: str) -> float | None:
        product = await self._fetch_card(product_id)
        return _extract_price(product)

    async def get_tags(self, product_id: str) -> list[str]:
        return await self._fetch_tags(int(product_id))

    async def get_stock(self, product_id: str) -> int | None:
        product = await self._fetch_card(product_id)
        return _extract_stock(product)
