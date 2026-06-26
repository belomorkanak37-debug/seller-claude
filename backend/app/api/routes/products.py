import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.providers.base import (
    CaptchaRequired,
    ProductNotFound,
    ProviderError,
    SourceUnavailable,
)
from app.providers.registry import UnknownMarketplace
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductPreview,
    ProductUpdate,
)
from app.schemas.review import ReviewOut
from app.services import products as svc

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


def _provider_http_error(exc: ProviderError) -> HTTPException:
    """Маппинг доменных ошибок провайдера в понятные HTTP-ответы."""
    if isinstance(exc, ProductNotFound):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден по артикулу")
    if isinstance(exc, CaptchaRequired):
        return HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Источник запросил капчу. Попробуйте позже.",
        )
    if isinstance(exc, SourceUnavailable):
        return HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
    if isinstance(exc, UnknownMarketplace):
        return HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return HTTPException(status.HTTP_502_BAD_GATEWAY, f"Ошибка источника: {exc}")


@router.get("/lookup", response_model=ProductPreview)
async def lookup_product(
    marketplace: str = Query(..., description="ozon | wildberries | yandex_market"),
    article: str = Query(..., min_length=1),
    user: User = Depends(get_current_user),
) -> ProductPreview:
    """Тянет живую карточку по артикулу для экрана «Это ваш товар?» (без сохранения)."""
    try:
        dto = await svc.fetch_product_dto(marketplace, article)
        review_dtos = await svc.fetch_reviews_dto(marketplace, dto.root_id)
    except ProviderError as exc:
        raise _provider_http_error(exc) from exc

    return ProductPreview(
        marketplace=dto.marketplace.value,
        article=dto.article,
        name=dto.name,
        price=dto.price,
        photo_url=dto.photo_url,
        rating=dto.rating,
        reviews_count=dto.reviews_count,
        tags=dto.tags,
        stock=dto.stock,
        url=dto.url,
        brand=dto.brand,
        reviews=svc._dto_to_review_out(review_dtos),
    )


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProductOut:
    """Подтверждение товара: сервер заново тянет реальные данные и сохраняет."""
    try:
        product = await svc.create_product_from_marketplace(
            session,
            user_id=user.id,
            marketplace=payload.marketplace,
            article=payload.article,
            cost_price=payload.cost_price,
        )
    except ProviderError as exc:
        raise _provider_http_error(exc) from exc
    return ProductOut.model_validate(product)


@router.get("", response_model=list[ProductOut])
async def list_products(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ProductOut]:
    products = await svc.list_user_products(session, user.id)
    return [ProductOut.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProductOut:
    product = await svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    return ProductOut.model_validate(product)


@router.get("/{product_id}/reviews", response_model=list[ReviewOut])
async def get_product_reviews(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ReviewOut]:
    product = await svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    reviews = await svc.get_stored_reviews(session, product_id)
    return [ReviewOut.model_validate(r) for r in reviews]


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProductOut:
    """Редактирование любых полей товара после добавления."""
    product = await svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(product, field, value)
    await session.commit()
    await session.refresh(product)
    return ProductOut.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    product = await svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    await session.delete(product)
    await session.commit()
