"""Трекинг позиций товара в поиске по ключевым запросам."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PositionSnapshot, Product
from app.providers.registry import get_provider
from app.services.keywords import extract_keywords

logger = logging.getLogger(__name__)

SEARCH_DEPTH = 100


def find_position(articles: list[str], target: str) -> int | None:
    """1-based позиция target в списке артикулов; None если не найден."""
    target = str(target)
    for i, a in enumerate(articles):
        if str(a) == target:
            return i + 1
    return None


def get_queries(product: Product) -> list[str]:
    """Запросы для трекинга: заданные продавцом или авто из названия."""
    if product.tracked_queries:
        return [q for q in product.tracked_queries if q and q.strip()]
    keywords = extract_keywords(product.name)
    return [" ".join(keywords)] if keywords else []


async def check_positions(
    session: AsyncSession, product: Product, store: bool = False
) -> list[dict]:
    """Проверяет позицию товара по каждому запросу (живой запрос к площадке)."""
    queries = get_queries(product)
    if not queries:
        return []
    provider = get_provider(product.marketplace)

    out: list[dict] = []
    for query in queries:
        try:
            results = await provider.search_competitors(
                query.split(), limit=SEARCH_DEPTH
            )
        except Exception as exc:  # noqa: BLE001
            logger.info("position check '%s': %s", query, exc)
            out.append({"query": query, "position": None})
            continue
        articles = [c.article for c in results if c.article]
        position = find_position(articles, product.article)
        out.append({"query": query, "position": position})
        if store:
            session.add(
                PositionSnapshot(
                    product_id=product.id, query=query, position=position
                )
            )
    if store:
        await session.commit()
    return out


async def get_history(session: AsyncSession, product_id: int) -> dict[str, list]:
    """История позиций, сгруппированная по запросу."""
    rows = (
        await session.execute(
            select(PositionSnapshot)
            .where(PositionSnapshot.product_id == product_id)
            .order_by(PositionSnapshot.captured_at)
        )
    ).scalars().all()
    grouped: dict[str, list] = {}
    for r in rows:
        grouped.setdefault(r.query, []).append(
            {"captured_at": r.captured_at, "position": r.position}
        )
    return grouped
