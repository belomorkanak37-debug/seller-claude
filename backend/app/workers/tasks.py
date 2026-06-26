"""Celery-задачи. Внутри используем async-провайдеры через asyncio.run."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.db.models import Product, User
from app.db.session import async_session_maker
from app.providers.base import ProviderError
from app.services import notifications as notify_svc
from app.services import price_history as price_svc
from app.services import products as products_svc
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


@celery_app.task(name="app.workers.tasks.check_new_reviews")
def check_new_reviews() -> dict:
    """Периодически проверяет новые отзывы по товарам и шлёт уведомления."""
    return _run(_check_new_reviews())


async def _check_new_reviews() -> dict:
    checked = 0
    notified = 0
    total_new = 0
    async with async_session_maker() as session:
        products = (await session.execute(select(Product))).scalars().all()
        for product in products:
            checked += 1
            try:
                new_count, new_reviews = await products_svc.sync_product_reviews(
                    session, product
                )
            except ProviderError as exc:
                logger.info("check_new_reviews %s: %s", product.id, exc)
                continue
            if new_count == 0:
                continue
            total_new += new_count
            user = await session.get(User, product.user_id)
            if user and await notify_svc.notify_new_reviews(
                session, user, product, new_reviews
            ):
                notified += 1
    return {
        "status": "ok",
        "checked": checked,
        "new_reviews": total_new,
        "notified": notified,
    }


@celery_app.task(name="app.workers.tasks.snapshot_all_prices")
def snapshot_all_prices() -> dict:
    """Ежедневный снимок цен по всем товарам и их конкурентам (история цен)."""
    return _run(_snapshot_all_prices())


async def _snapshot_all_prices() -> dict:
    async with async_session_maker() as session:
        return await price_svc.snapshot_all(session)
