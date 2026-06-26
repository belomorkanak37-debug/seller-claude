"""Сравнение карточки с конкурентами и SEO-помощник."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.services.keywords import _is_meaningful, _TOKEN_RE


@dataclass
class CardMetrics:
    has_photo: bool
    rating: float
    reviews_count: int
    tags_count: int
    price: float | None
    name_length: int


def card_metrics(obj) -> CardMetrics:
    """obj — Product или Competitor (одинаковые поля)."""
    tags = obj.tags or []
    return CardMetrics(
        has_photo=bool(obj.photo_url),
        rating=float(obj.rating or 0),
        reviews_count=int(obj.reviews_count or 0),
        tags_count=len(tags),
        price=float(obj.price) if obj.price is not None else None,
        name_length=len(obj.name or ""),
    )


@dataclass
class Comparison:
    product: CardMetrics
    competitors_avg: dict
    recommendations: list[str] = field(default_factory=list)


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def compare_cards(product, competitors) -> Comparison:
    pm = card_metrics(product)
    cms = [card_metrics(c) for c in competitors]

    avg = {
        "rating": _avg([c.rating for c in cms]),
        "reviews_count": round(_avg([c.reviews_count for c in cms])),
        "tags_count": round(_avg([c.tags_count for c in cms])),
        "price": _avg([c.price for c in cms if c.price is not None]),
        "name_length": round(_avg([c.name_length for c in cms])),
    }

    rec: list[str] = []
    if not pm.has_photo:
        rec.append("Добавьте главное фото — у вас его нет.")
    if cms:
        if pm.rating and avg["rating"] and pm.rating < avg["rating"]:
            rec.append(
                f"Рейтинг ниже среднего у конкурентов ({pm.rating} против {avg['rating']})."
            )
        if pm.reviews_count < avg["reviews_count"]:
            rec.append(
                f"Меньше отзывов, чем у конкурентов ({pm.reviews_count} против "
                f"~{avg['reviews_count']}) — стимулируйте отзывы."
            )
        if pm.tags_count < avg["tags_count"]:
            rec.append(
                f"Заполните характеристики: у вас {pm.tags_count}, у конкурентов "
                f"~{avg['tags_count']}."
            )
        if pm.name_length < avg["name_length"] * 0.8 and avg["name_length"]:
            rec.append(
                "Название короче, чем у конкурентов — добавьте ключевые свойства."
            )
        if (
            pm.price is not None
            and avg["price"]
            and pm.price > avg["price"] * 1.1
        ):
            rec.append(
                f"Цена выше средней по конкурентам ({pm.price} против {avg['price']})."
            )
    if not rec:
        rec.append("Карточка в порядке относительно конкурентов 👍")

    return Comparison(product=pm, competitors_avg=avg, recommendations=rec)


@dataclass
class SeoResult:
    suggested_keywords: list[str]
    score: int
    tips: list[str] = field(default_factory=list)


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall((text or "").lower()) if _is_meaningful(t)]


def suggest_keywords(
    product_name: str, competitor_names: list[str], limit: int = 8
) -> list[str]:
    """Частотные ключевые слова из названий конкурентов, которых нет у меня."""
    own = set(_tokens(product_name))
    counter: Counter[str] = Counter()
    for name in competitor_names:
        for tok in set(_tokens(name)):
            counter[tok] += 1
    suggestions = [w for w, _ in counter.most_common() if w not in own]
    return suggestions[:limit]


def score_card(metrics: CardMetrics) -> tuple[int, list[str]]:
    """Оценка карточки 0–100 + советы по улучшению."""
    score = 0
    tips: list[str] = []

    if metrics.has_photo:
        score += 20
    else:
        tips.append("Добавьте фото товара.")

    if metrics.rating >= 4.5:
        score += 20
    elif metrics.rating >= 4.0:
        score += 12
    else:
        tips.append("Поработайте над рейтингом (качество, ответы на отзывы).")

    if metrics.reviews_count >= 100:
        score += 20
    elif metrics.reviews_count >= 20:
        score += 12
    else:
        tips.append("Мало отзывов — стимулируйте покупателей оставлять отзывы.")

    if metrics.tags_count >= 10:
        score += 20
    elif metrics.tags_count >= 5:
        score += 12
    else:
        tips.append("Заполните больше характеристик товара.")

    if metrics.name_length >= 40:
        score += 20
    elif metrics.name_length >= 20:
        score += 12
    else:
        tips.append("Сделайте название информативнее (категория + свойства).")

    return score, tips


def build_seo(product, competitors) -> SeoResult:
    suggestions = suggest_keywords(
        product.name, [c.name for c in competitors]
    )
    score, tips = score_card(card_metrics(product))
    return SeoResult(suggested_keywords=suggestions, score=score, tips=tips)
