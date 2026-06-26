"""История цен: снимки цен товаров и конкурентов + выборка для графика.

График строится ТОЛЬКО из реально накопленных снапшотов — никаких
синтетических данных. Снимки делает ежедневная Celery-задача; есть и ручной
снимок, чтобы продавец мог начать накапливать историю сразу.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Competitor, PriceSnapshot, Product
from app.providers.base import ProviderError
from app.providers.registry import get_provider

logger = logging.getLogger(__name__)


async def _snapshot_price(
    session: AsyncSession,
    marketplace: str,
    article: str | None,
    *,
    product_id: int | None = None,
    competitor_id: int | None = None,
) -> bool:
    if not article:
        return False
    try:
        provider = get_provider(marketplace)
        price = await provider.get_price(article)
    except ProviderError as exc:
        logger.info("snapshot price skip (%s/%s): %s", marketplace, article, exc)
        return False
    if price is None:
        return False
    session.add(
        PriceSnapshot(
            product_id=product_id, competitor_id=competitor_id, price=price
        )
    )
    return True


async def snapshot_for_product(
    session: AsyncSession, product: Product
) -> dict:
    """Снимает цену товара и всех его конкурентов прямо сейчас."""
    saved_product = await _snapshot_price(
        session, product.marketplace, product.article, product_id=product.id
    )

    competitors = (
        await session.execute(
            select(Competitor).where(Competitor.product_id == product.id)
        )
    ).scalars().all()

    saved_competitors = 0
    for c in competitors:
        if await _snapshot_price(
            session, c.marketplace, c.article, competitor_id=c.id
        ):
            saved_competitors += 1

    await session.commit()
    return {
        "product": 1 if saved_product else 0,
        "competitors": saved_competitors,
    }


async def snapshot_all(session: AsyncSession) -> dict:
    """Снимки по всем товарам и их конкурентам (для ежедневной задачи)."""
    products = (await session.execute(select(Product))).scalars().all()
    totals = {"products": 0, "competitors": 0}
    for product in products:
        res = await snapshot_for_product(session, product)
        totals["products"] += res["product"]
        totals["competitors"] += res["competitors"]
    return {"status": "ok", **totals}


async def get_history(session: AsyncSession, product: Product) -> dict:
    """Возвращает временные ряды цен товара и конкурентов из снапшотов."""
    product_points = (
        await session.execute(
            select(PriceSnapshot)
            .where(PriceSnapshot.product_id == product.id)
            .order_by(PriceSnapshot.captured_at)
        )
    ).scalars().all()

    competitors = (
        await session.execute(
            select(Competitor).where(Competitor.product_id == product.id)
        )
    ).scalars().all()

    competitor_series = []
    for c in competitors:
        points = (
            await session.execute(
                select(PriceSnapshot)
                .where(PriceSnapshot.competitor_id == c.id)
                .order_by(PriceSnapshot.captured_at)
            )
        ).scalars().all()
        competitor_series.append((c, points))

    return {
        "product_points": product_points,
        "competitor_series": competitor_series,
    }
