"""Бизнес-логика по конкурентам: поиск по ключевым словам и сохранение."""

from __future__ import annotations

import logging

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Competitor, Product, Review
from app.providers.base import CompetitorDTO, ProviderError, ReviewDTO
from app.providers.registry import get_provider
from app.schemas.competitor import CompetitorCreate
from app.services.keywords import extract_keywords

logger = logging.getLogger(__name__)

REVIEWS_LIMIT = 30


async def search_for_product(
    product: Product, limit: int = 10
) -> tuple[list[str], list[CompetitorDTO]]:
    """Выделяет ключевые слова из названия и ищет конкурентов на той же площадке."""
    keywords = extract_keywords(product.name)
    if not keywords:
        return [], []
    provider = get_provider(product.marketplace)
    results = await provider.search_competitors(keywords, limit=limit + 1)
    # Исключаем собственный товар из выдачи
    competitors = [
        c for c in results if str(c.article) != str(product.article)
    ][:limit]
    return keywords, competitors


async def add_competitor(
    session: AsyncSession, product_id: int, payload: CompetitorCreate
) -> Competitor:
    """Сохраняет конкурента и best-effort подтягивает его теги и отзывы."""
    competitor = Competitor(
        product_id=product_id,
        marketplace=payload.marketplace,
        article=payload.article,
        url=payload.url,
        name=payload.name,
        photo_url=payload.photo_url,
        price=payload.price,
        rating=payload.rating,
        reviews_count=payload.reviews_count,
        note=payload.note,
    )
    session.add(competitor)
    await session.flush()

    # Реальные теги и отзывы конкурента (не критично, если источник недоступен)
    if payload.article:
        try:
            await _enrich_competitor(session, competitor, payload.marketplace,
                                     payload.article)
        except ProviderError as exc:
            logger.info("Обогащение конкурента %s пропущено: %s", competitor.id, exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ошибка обогащения конкурента %s: %s", competitor.id, exc)

    await session.commit()
    await session.refresh(competitor)
    return competitor


async def _enrich_competitor(
    session: AsyncSession, competitor: Competitor, marketplace: str, article: str
) -> None:
    provider = get_provider(marketplace)
    dto = await provider.get_product(article)
    if dto.tags:
        competitor.tags = dto.tags
    if competitor.rating is None and dto.rating is not None:
        competitor.rating = dto.rating
    if competitor.reviews_count is None and dto.reviews_count is not None:
        competitor.reviews_count = dto.reviews_count

    review_dtos: list[ReviewDTO] = []
    if dto.root_id:
        review_dtos = await provider.get_reviews(dto.root_id, limit=REVIEWS_LIMIT)
    await _store_competitor_reviews(session, competitor.id, review_dtos)


async def _store_competitor_reviews(
    session: AsyncSession, competitor_id: int, dtos: list[ReviewDTO]
) -> None:
    await session.execute(
        delete(Review).where(Review.competitor_id == competitor_id)
    )
    for d in dtos:
        session.add(
            Review(
                competitor_id=competitor_id,
                external_id=d.external_id,
                source=d.source,
                author=d.author,
                text=d.text,
                rating=d.rating,
                published_at=d.published_at,
            )
        )


async def list_competitors(
    session: AsyncSession, product_id: int
) -> list[Competitor]:
    result = await session.execute(
        select(Competitor)
        .where(Competitor.product_id == product_id)
        .order_by(Competitor.created_at.desc())
    )
    return list(result.scalars().all())


async def get_user_competitor(
    session: AsyncSession, user_id: int, competitor_id: int
) -> Competitor | None:
    """Конкурент, принадлежащий товару текущего пользователя."""
    result = await session.execute(
        select(Competitor)
        .join(Product, Competitor.product_id == Product.id)
        .where(Competitor.id == competitor_id, Product.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_competitor_reviews(
    session: AsyncSession, competitor_id: int
) -> list[Review]:
    result = await session.execute(
        select(Review)
        .where(Review.competitor_id == competitor_id)
        .order_by(Review.published_at.desc().nullslast())
    )
    return list(result.scalars().all())
