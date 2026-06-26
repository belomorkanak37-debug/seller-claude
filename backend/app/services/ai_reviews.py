"""AI-функции по отзывам: ответы, тональность/жалобы, анализ конкурентов."""

from __future__ import annotations

from app.ai.base import LLMProvider
from app.db.models import Product, Review


def _format_reviews(reviews: list[Review], limit: int = 40) -> str:
    lines = []
    for i, r in enumerate(reviews[:limit], 1):
        rating = f"{r.rating}★" if r.rating is not None else "—"
        text = (r.text or "").strip().replace("\n", " ")
        lines.append(f"{i}. [{rating}] {text}")
    return "\n".join(lines) if lines else "(нет отзывов)"


async def generate_reply(
    llm: LLMProvider, product: Product, review: Review
) -> str:
    """Генерирует вежливый ответ продавца на отзыв (особенно негатив)."""
    system = (
        "Ты — представитель продавца на маркетплейсе. Пиши вежливые, "
        "человечные ответы на отзывы покупателей на русском языке. Для "
        "негатива: поблагодари, признай проблему, предложи решение, без "
        "шаблонности и без обещаний, которые нельзя выполнить. 2–5 предложений."
    )
    rating = f"{review.rating}★" if review.rating is not None else "без оценки"
    user = (
        f"Товар: {product.name}\n"
        f"Отзыв ({rating}) от {review.author or 'покупателя'}:\n"
        f"{(review.text or '').strip()}\n\n"
        "Напиши ответ продавца."
    )
    return await llm.complete(system, user, max_tokens=600)


async def analyze_reviews(
    llm: LLMProvider, product: Product, reviews: list[Review]
) -> dict:
    """Тональность + повторяющиеся жалобы + рекомендации по моему товару."""
    system = (
        "Ты — аналитик отзывов маркетплейса. Проанализируй отзывы и верни JSON "
        "со схемой: {\"sentiment\": {\"positive\": int, \"neutral\": int, "
        "\"negative\": int}, \"common_complaints\": [строки], "
        "\"suggestions\": [строки]}. common_complaints — повторяющиеся жалобы, "
        "suggestions — что улучшить в товаре/карточке. По-русски, кратко."
    )
    user = f"Товар: {product.name}\nОтзывы:\n{_format_reviews(reviews)}"
    data = await llm.complete_json(system, user, max_tokens=1500)
    return _normalize_analysis(data)


async def analyze_competitor_reviews(
    llm: LLMProvider, product: Product, reviews: list[Review]
) -> dict:
    """За что хвалят/ругают конкурентов и чем можно выделиться."""
    system = (
        "Ты — аналитик конкурентов на маркетплейсе. По отзывам конкурентов "
        "верни JSON: {\"praise\": [строки], \"criticism\": [строки], "
        "\"differentiation\": [строки]}. praise — за что хвалят, criticism — "
        "за что ругают, differentiation — идеи, чем выделиться нашему товару. "
        "По-русски, кратко, по пунктам."
    )
    user = f"Наш товар: {product.name}\nОтзывы конкурентов:\n{_format_reviews(reviews)}"
    data = await llm.complete_json(system, user, max_tokens=1500)
    return _normalize_competitor(data)


def _as_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if v]
    if value:
        return [str(value)]
    return []


def _normalize_analysis(data) -> dict:
    data = data if isinstance(data, dict) else {}
    sent = data.get("sentiment") or {}
    return {
        "sentiment": {
            "positive": int(sent.get("positive", 0) or 0),
            "neutral": int(sent.get("neutral", 0) or 0),
            "negative": int(sent.get("negative", 0) or 0),
        },
        "common_complaints": _as_list(data.get("common_complaints")),
        "suggestions": _as_list(data.get("suggestions")),
    }


def _normalize_competitor(data) -> dict:
    data = data if isinstance(data, dict) else {}
    return {
        "praise": _as_list(data.get("praise")),
        "criticism": _as_list(data.get("criticism")),
        "differentiation": _as_list(data.get("differentiation")),
    }
