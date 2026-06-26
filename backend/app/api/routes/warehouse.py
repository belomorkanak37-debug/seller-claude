from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas.warehouse import WarehouseForecastOut, WarehouseParamsIn
from app.services import products as products_svc
from app.services import warehouse as svc

router = APIRouter(prefix="/products", tags=["warehouse"])


def _to_out(f) -> WarehouseForecastOut:
    return WarehouseForecastOut(
        stock=f.stock,
        daily_sales=f.daily_sales,
        days_left=f.days_left,
        recommended_supply=f.recommended_supply,
        status=f.status,
        params=WarehouseParamsIn(
            daily_sales=f.params.daily_sales,
            lead_time_days=f.params.lead_time_days,
            target_cover_days=f.params.target_cover_days,
            low_stock_threshold_days=f.params.low_stock_threshold_days,
        ),
    )


@router.get("/{product_id}/warehouse", response_model=WarehouseForecastOut)
async def get_warehouse(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WarehouseForecastOut:
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    return _to_out(svc.forecast_for_product(product))


@router.put("/{product_id}/warehouse", response_model=WarehouseForecastOut)
async def save_warehouse(
    product_id: int,
    payload: WarehouseParamsIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WarehouseForecastOut:
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    forecast = await svc.save_params(
        session, product, svc.WarehouseParams(**payload.model_dump())
    )
    return _to_out(forecast)
