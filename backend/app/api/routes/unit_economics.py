from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas.unit_economics import EconomicsOut, EconomicsParamsIn
from app.services import products as products_svc
from app.services import unit_economics as svc

router = APIRouter(prefix="/products", tags=["unit-economics"])


def _to_out(result, params: EconomicsParamsIn) -> EconomicsOut:
    return EconomicsOut(
        price=result.price,
        cost_price=result.cost_price,
        params=params,
        breakdown=result.breakdown,
        total_costs=result.total_costs,
        net_profit=result.net_profit,
        margin_pct=result.margin_pct,
        is_profitable=result.is_profitable,
    )


@router.get("/{product_id}/unit-economics", response_model=EconomicsOut)
async def get_unit_economics(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> EconomicsOut:
    """Текущий расчёт по сохранённым параметрам (или нулевым по умолчанию)."""
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")

    row = await svc.get_or_default(session, product_id)
    params = EconomicsParamsIn(
        commission_pct=float(row.commission_pct or 0) if row else 0,
        logistics_cost=float(row.logistics_cost or 0) if row else 0,
        storage_cost=float(row.storage_cost or 0) if row else 0,
        acquiring_pct=float(row.acquiring_pct or 0) if row else 0,
        returns_pct=float(row.returns_pct or 0) if row else 0,
        tax_pct=float(row.tax_pct or 0) if row else 0,
    )
    result = svc.compute_economics(
        float(product.price) if product.price is not None else None,
        float(product.cost_price) if product.cost_price is not None else None,
        svc.EconomicsParams(**params.model_dump()),
    )
    return _to_out(result, params)


@router.put("/{product_id}/unit-economics", response_model=EconomicsOut)
async def save_unit_economics(
    product_id: int,
    payload: EconomicsParamsIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> EconomicsOut:
    """Сохраняет параметры и возвращает пересчитанный результат."""
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")

    result = await svc.save_and_compute(
        session, product, svc.EconomicsParams(**payload.model_dump())
    )
    return _to_out(result, payload)
