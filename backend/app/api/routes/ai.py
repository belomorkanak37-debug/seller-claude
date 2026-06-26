import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import LLMError, LLMNotConfigured
from app.ai.factory import get_llm
from app.api.deps import get_current_user
from app.db.models import Competitor, Product, Review, User
from app.db.session import get_session
from app.schemas.ai import (
    CompetitorAnalysisOut,
    ReplyOut,
    ReviewAnalysisOut,
)
from app.services import ai_reviews as ai_svc
from app.services import products as products_svc

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ai"])


def _llm_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LLMNotConfigured):
        return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    if isinstance(exc, LLMError):
        return HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
    return HTTPException(status.HTTP_502_BAD_GATEWAY, f"Ошибка AI: {exc}")


async def _get_user_review(
    session: AsyncSession, user_id: int, review_id: int
) -> tuple[Review, Product] | None:
    """Отзыв и связанный товар продавца (по моему товару или конкуренту)."""
    review = await session.get(Review, review_id)
    if review is None:
        return None
    product: Product | None = None
    if review.product_id:
        product = await products_svc.get_user_product(
            session, user_id, review.product_id
        )
    elif review.competitor_id:
        competitor = await session.get(Competitor, review.competitor_id)
        if competitor:
            product = await products_svc.get_user_product(
                session, user_id, competitor.product_id
            )
    if product is None:
        return None
    return review, product


async def _competitor_reviews(session: AsyncSession, product_id: int) -> list[Review]:
    rows = await session.execute(
        select(Review)
        .join(Competitor, Review.competitor_id == Competitor.id)
        .where(Competitor.product_id == product_id)
        .order_by(Review.published_at.desc().nullslast())
    )
    return list(rows.scalars().all())


@router.post("/reviews/{review_id}/reply", response_model=ReplyOut)
async def generate_reply(
    review_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReplyOut:
    """Генерирует ответ продавца на отзыв (особенно негатив)."""
    found = await _get_user_review(session, user.id, review_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Отзыв не найден")
    review, product = found
    try:
        reply = await ai_svc.generate_reply(get_llm(), product, review)
    except (LLMError, LLMNotConfigured) as exc:
        raise _llm_http_error(exc) from exc
    return ReplyOut(reply=reply)


@router.post("/products/{product_id}/reviews/analyze", response_model=ReviewAnalysisOut)
async def analyze_reviews(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReviewAnalysisOut:
    """Тональность и повторяющиеся жалобы по моему товару."""
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    reviews = await products_svc.get_stored_reviews(session, product_id)
    if not reviews:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Нет отзывов для анализа — сначала обновите отзывы товара.",
        )
    try:
        result = await ai_svc.analyze_reviews(get_llm(), product, reviews)
    except (LLMError, LLMNotConfigured) as exc:
        raise _llm_http_error(exc) from exc
    return ReviewAnalysisOut(**result)


@router.post(
    "/products/{product_id}/competitors/analyze",
    response_model=CompetitorAnalysisOut,
)
async def analyze_competitors(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompetitorAnalysisOut:
    """Анализ отзывов конкурентов: за что хвалят/ругают и чем выделиться."""
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    reviews = await _competitor_reviews(session, product_id)
    if not reviews:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Нет отзывов конкурентов — добавьте конкурентов с отзывами.",
        )
    try:
        result = await ai_svc.analyze_competitor_reviews(get_llm(), product, reviews)
    except (LLMError, LLMNotConfigured) as exc:
        raise _llm_http_error(exc) from exc
    return CompetitorAnalysisOut(**result)
