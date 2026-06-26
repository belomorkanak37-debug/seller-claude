"""Чистые функции парсинга (без сети) — легко тестируются на сэмплах.

Делаем ставку на устойчивые к смене вёрстки источники:
- ld+json (schema.org/Product) — есть и у Ozon, и у Я.Маркета, меняется редко;
- composer-api widgetStates у Ozon — основной структурированный источник.
"""

from __future__ import annotations

import json
import re


def _to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    # "1 299,90 ₽" / "1299.90" -> 1299.9
    s = re.sub(r"[^\d,.\-]", "", str(value)).replace(",", ".")
    if not s or s in {".", "-"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _to_int(value) -> int | None:
    f = _to_float(value)
    return int(f) if f is not None else None


_LDJSON_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _iter_ldjson_objects(html: str):
    for match in _LDJSON_RE.finditer(html):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            yield from data
        elif isinstance(data, dict):
            # @graph контейнер
            if "@graph" in data and isinstance(data["@graph"], list):
                yield from data["@graph"]
            else:
                yield data


def parse_ldjson_product(html: str) -> dict:
    """Достаёт поля товара из ld+json schema.org/Product. Пустой dict, если нет."""
    for obj in _iter_ldjson_objects(html):
        types = obj.get("@type")
        types = types if isinstance(types, list) else [types]
        if "Product" not in types:
            continue

        image = obj.get("image")
        if isinstance(image, list):
            image = image[0] if image else None
        if isinstance(image, dict):
            image = image.get("url")

        offers = obj.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = _to_float(offers.get("price")) if isinstance(offers, dict) else None

        rating = None
        reviews_count = None
        agg = obj.get("aggregateRating")
        if isinstance(agg, dict):
            rating = _to_float(agg.get("ratingValue"))
            reviews_count = _to_int(
                agg.get("reviewCount") or agg.get("ratingCount")
            )

        return {
            "name": obj.get("name"),
            "photo_url": image,
            "price": price,
            "rating": rating,
            "reviews_count": reviews_count,
            "brand": (obj.get("brand") or {}).get("name")
            if isinstance(obj.get("brand"), dict)
            else obj.get("brand"),
        }
    return {}


def _ozon_widget_states(composer_json: dict) -> dict[str, dict]:
    """Раскрывает widgetStates: значения приходят JSON-строками."""
    states = composer_json.get("widgetStates") or {}
    result: dict[str, dict] = {}
    for key, raw in states.items():
        if not isinstance(raw, str):
            continue
        try:
            result[key] = json.loads(raw)
        except json.JSONDecodeError:
            continue
    return result


def _find_by_prefix(states: dict[str, dict], prefix: str) -> dict | None:
    for key, value in states.items():
        if key.startswith(prefix):
            return value
    return None


def parse_ozon_composer(composer_json: dict) -> dict:
    """Парсит карточку Ozon из composer-api widgetStates."""
    states = _ozon_widget_states(composer_json)
    out: dict = {}

    heading = _find_by_prefix(states, "webProductHeading")
    if heading:
        out["name"] = heading.get("title")

    price_w = _find_by_prefix(states, "webPrice")
    if price_w:
        out["price"] = _to_float(
            price_w.get("cardPrice")
            or price_w.get("price")
            or price_w.get("priceWithCard")
        )

    score = _find_by_prefix(states, "webReviewProductScore") or _find_by_prefix(
        states, "webSingleProductScore"
    )
    if score:
        out["rating"] = _to_float(score.get("totalScore") or score.get("score"))
        out["reviews_count"] = _to_int(
            score.get("reviewsCount") or score.get("commentsCount")
        )

    gallery = _find_by_prefix(states, "webGallery")
    if gallery:
        images = gallery.get("images") or gallery.get("coverImage")
        if isinstance(images, list) and images:
            first = images[0]
            out["photo_url"] = (
                first.get("src") if isinstance(first, dict) else first
            )
        elif isinstance(images, str):
            out["photo_url"] = images

    chars = _find_by_prefix(states, "webCharacteristics")
    if chars:
        tags: list[str] = []
        for block in chars.get("characteristics", []) or []:
            for item in block.get("short", []) or block.get("values", []) or []:
                name = item.get("name") or block.get("title")
                val = item.get("text") or item.get("value")
                if name and val:
                    tags.append(f"{name}: {val}")
                elif val:
                    tags.append(str(val))
        out["tags"] = tags[:40]

    return out
