from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas.price_history import (
    PriceHistoryOut,
    PricePoint,
    PriceSeries,
    SnapshotResult,
)
from app.services import price_history as svc
from app.services import products as products_svc

router = APIRouter(prefix="/products", tags=["price-history"])


@router.get("/{product_id}/price-history", response_model=PriceHistoryOut)
async def price_history(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PriceHistoryOut:
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")

    data = await svc.get_history(session, product)
    product_series = PriceSeries(
        label=product.name,
        points=[
            PricePoint(captured_at=p.captured_at, price=float(p.price))
            for p in data["product_points"]
        ],
    )
    competitors = [
        PriceSeries(
            label=c.name,
            competitor_id=c.id,
            points=[
                PricePoint(captured_at=p.captured_at, price=float(p.price))
                for p in points
            ],
        )
        for c, points in data["competitor_series"]
    ]
    return PriceHistoryOut(product=product_series, competitors=competitors)


@router.post("/{product_id}/price-snapshot", response_model=SnapshotResult)
async def take_snapshot(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SnapshotResult:
    """Ручной снимок цен товара и конкурентов (чтобы начать копить историю)."""
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    res = await svc.snapshot_for_product(session, product)
    return SnapshotResult(**res)
