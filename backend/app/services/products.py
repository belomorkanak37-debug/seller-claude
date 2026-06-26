"""Бизнес-логика по товарам: работает только через MarketplaceProvider."""

from __future__ import annotations

import logging

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product, Review
from app.providers.base import ProductDTO, ReviewDTO
from app.providers.registry import get_provider
from app.schemas.review import ReviewOut

logger = logging.getLogger(__name__)

# Сколько отзывов тянем/храним на Этапе 1 (полная работа с отзывами — Этап 4).
REVIEWS_LIMIT = 30


async def fetch_product_dto(marketplace: str, article: str) -> ProductDTO:
    provider = get_provider(marketplace)
    return await provider.get_product(article)


async def fetch_reviews_dto(
    marketplace: str, root_id: str | None, limit: int = REVIEWS_LIMIT
) -> list[ReviewDTO]:
    if not root_id:
        return []
    provider = get_provider(marketplace)
    return await provider.get_reviews(root_id, limit=limit)


def _dto_to_review_out(dtos: list[ReviewDTO]) -> list[ReviewOut]:
    return [
        ReviewOut(
            external_id=d.external_id,
            source=d.source,
            author=d.author,
            text=d.text,
            rating=d.rating,
            published_at=d.published_at,
        )
        for d in dtos
    ]


async def create_product_from_marketplace(
    session: AsyncSession,
    user_id: int,
    marketplace: str,
    article: str,
    cost_price: float | None = None,
) -> Product:
    """Тянет реальные данные карточки и сохраняет товар + его отзывы."""
    dto = await fetch_product_dto(marketplace, article)

    product = Product(
        user_id=user_id,
        marketplace=dto.marketplace.value,
        article=dto.article,
        name=dto.name,
        photo_url=dto.photo_url,
        price=dto.price,
        rating=dto.rating,
        reviews_count=dto.reviews_count,
        tags=dto.tags or None,
        stock=dto.stock,
        root_id=dto.root_id,
        cost_price=cost_price,
    )
    session.add(product)
    await session.flush()  # получаем product.id

    # Подтягиваем реальные отзывы (best-effort: ошибка отзывов не валит товар)
    try:
        review_dtos = await fetch_reviews_dto(marketplace, dto.root_id)
        await _store_product_reviews(session, product.id, review_dtos)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Не удалось сохранить отзывы товара %s: %s", product.id, exc)

    await session.commit()
    await session.refresh(product)
    return product


async def _store_product_reviews(
    session: AsyncSession, product_id: int, dtos: list[ReviewDTO]
) -> None:
    # Перезаписываем набор отзывов товара (на Этапе 4 сделаем инкрементально)
    await session.execute(delete(Review).where(Review.product_id == product_id))
    for d in dtos:
        session.add(
            Review(
                product_id=product_id,
                external_id=d.external_id,
                source=d.source,
                author=d.author,
                text=d.text,
                rating=d.rating,
                published_at=d.published_at,
            )
        )


async def sync_product_reviews(
    session: AsyncSession, product: Product
) -> tuple[int, list[Review]]:
    """Инкрементально подтягивает новые отзывы товара.

    Возвращает (кол-во новых, список новых Review). Дедуп по external_id.
    Используется ручным обновлением и периодической задачей уведомлений.
    """
    # root_id нужен для отзывов; если не сохранён — берём из карточки
    root_id = product.root_id
    provider = get_provider(product.marketplace)
    if not root_id:
        dto = await provider.get_product(product.article)
        root_id = dto.root_id
        if root_id:
            product.root_id = root_id
    if not root_id:
        return 0, []

    live = await provider.get_reviews(root_id, limit=REVIEWS_LIMIT)

    existing = await session.execute(
        select(Review.external_id).where(Review.product_id == product.id)
    )
    known: set[str] = {e for (e,) in existing.all() if e}

    new_reviews: list[Review] = []
    for d in live:
        if not d.external_id or d.external_id in known:
            continue
        review = Review(
            product_id=product.id,
            external_id=d.external_id,
            source=d.source,
            author=d.author,
            text=d.text,
            rating=d.rating,
            published_at=d.published_at,
        )
        session.add(review)
        new_reviews.append(review)
        known.add(d.external_id)

    await session.commit()
    for r in new_reviews:
        await session.refresh(r)
    return len(new_reviews), new_reviews


async def get_user_product(
    session: AsyncSession, user_id: int, product_id: int
) -> Product | None:
    result = await session.execute(
        select(Product).where(
            Product.id == product_id, Product.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def list_user_products(
    session: AsyncSession, user_id: int
) -> list[Product]:
    result = await session.execute(
        select(Product)
        .where(Product.user_id == user_id)
        .order_by(Product.created_at.desc())
    )
    return list(result.scalars().all())


async def get_stored_reviews(
    session: AsyncSession, product_id: int
) -> list[Review]:
    result = await session.execute(
        select(Review)
        .where(Review.product_id == product_id)
        .order_by(Review.published_at.desc().nullslast())
    )
    return list(result.scalars().all())
