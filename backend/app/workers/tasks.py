"""Celery-задачи. Внутри используем async-провайдеры через asyncio.run."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.db.models import PriceSnapshot, Product
from app.db.session import async_session_maker
from app.providers.base import ProviderError
from app.providers.registry import get_provider
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    """Запускает корутину из синхронной Celery-задачи."""
    return asyncio.run(coro)


@celery_app.task(name="app.workers.tasks.refresh_product")
def refresh_product(product_id: int) -> dict:
    """Перетягивает живые данные карточки и обновляет товар в БД."""
    return _run(_refresh_product(product_id))


async def _refresh_product(product_id: int) -> dict:
    async with async_session_maker() as session:
        product = await session.get(Product, product_id)
        if product is None:
            return {"product_id": product_id, "status": "not_found"}
        try:
            provider = get_provider(product.marketplace)
            dto = await provider.get_product(product.article)
        except ProviderError as exc:
            logger.warning("refresh_product %s: %s", product_id, exc)
            return {"product_id": product_id, "status": "source_error", "error": str(exc)}

        product.name = dto.name
        product.price = dto.price
        product.rating = dto.rating
        product.reviews_count = dto.reviews_count
        product.stock = dto.stock
        if dto.tags:
            product.tags = dto.tags
        await session.commit()
        return {"product_id": product_id, "status": "ok", "price": float(dto.price or 0)}


@celery_app.task(name="app.workers.tasks.snapshot_all_prices")
def snapshot_all_prices() -> dict:
    """Снимок цен по всем товарам (для истории цен, Этап 5)."""
    return _run(_snapshot_all_prices())


async def _snapshot_all_prices() -> dict:
    saved = 0
    async with async_session_maker() as session:
        products = (await session.execute(select(Product))).scalars().all()
        for product in products:
            try:
                provider = get_provider(product.marketplace)
                price = await provider.get_price(product.article)
            except ProviderError as exc:
                logger.warning("snapshot %s: %s", product.id, exc)
                continue
            if price is not None:
                session.add(PriceSnapshot(product_id=product.id, price=price))
                saved += 1
        await session.commit()
    return {"status": "ok", "snapshots": saved}
