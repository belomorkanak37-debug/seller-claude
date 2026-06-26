import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.routes.products import _provider_http_error
from app.db.models import User
from app.db.session import get_session
from app.providers.base import ProviderError
from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorOut,
    CompetitorPreview,
    CompetitorSearchResponse,
    CompetitorUpdate,
)
from app.schemas.review import ReviewOut
from app.services import competitors as svc
from app.services import products as products_svc

logger = logging.getLogger(__name__)
router = APIRouter(tags=["competitors"])


@router.get(
    "/products/{product_id}/competitors/search",
    response_model=CompetitorSearchResponse,
)
async def search_competitors(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompetitorSearchResponse:
    """Выделяет ключевые слова из названия товара и ищет конкурентов."""
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    try:
        keywords, dtos = await svc.search_for_product(product)
    except ProviderError as exc:
        raise _provider_http_error(exc) from exc

    return CompetitorSearchResponse(
        keywords=keywords,
        competitors=[
            CompetitorPreview(
                marketplace=c.marketplace.value,
                article=c.article,
                name=c.name,
                price=c.price,
                photo_url=c.photo_url,
                rating=c.rating,
                reviews_count=c.reviews_count,
                url=c.url,
            )
            for c in dtos
        ],
    )


@router.post(
    "/products/{product_id}/competitors",
    response_model=CompetitorOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_competitor(
    product_id: int,
    payload: CompetitorCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompetitorOut:
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    competitor = await svc.add_competitor(session, product_id, payload)
    return CompetitorOut.model_validate(competitor)


@router.get(
    "/products/{product_id}/competitors",
    response_model=list[CompetitorOut],
)
async def list_competitors(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[CompetitorOut]:
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    competitors = await svc.list_competitors(session, product_id)
    return [CompetitorOut.model_validate(c) for c in competitors]


@router.get(
    "/competitors/{competitor_id}/reviews",
    response_model=list[ReviewOut],
)
async def competitor_reviews(
    competitor_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ReviewOut]:
    competitor = await svc.get_user_competitor(session, user.id, competitor_id)
    if competitor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Конкурент не найден")
    reviews = await svc.get_competitor_reviews(session, competitor_id)
    return [ReviewOut.model_validate(r) for r in reviews]


@router.patch("/competitors/{competitor_id}", response_model=CompetitorOut)
async def update_competitor(
    competitor_id: int,
    payload: CompetitorUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompetitorOut:
    """Редактирование конкурента, в т.ч. поле «Заметка»."""
    competitor = await svc.get_user_competitor(session, user.id, competitor_id)
    if competitor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Конкурент не найден")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(competitor, field, value)
    await session.commit()
    await session.refresh(competitor)
    return CompetitorOut.model_validate(competitor)


@router.delete(
    "/competitors/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_competitor(
    competitor_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    competitor = await svc.get_user_competitor(session, user.id, competitor_id)
    if competitor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Конкурент не найден")
    await session.delete(competitor)
    await session.commit()
