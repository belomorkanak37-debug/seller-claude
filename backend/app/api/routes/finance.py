from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import Payout, User
from app.db.session import get_session
from app.schemas.finance import (
    PayoutIn,
    PayoutOut,
    PayoutsOverviewOut,
    PayoutsSummaryOut,
    PnLOut,
)
from app.services import finance as svc
from app.services import pricing as pricing_svc
from app.services import products as products_svc

router = APIRouter(tags=["finance"])


@router.get("/payouts", response_model=PayoutsOverviewOut)
async def get_payouts(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PayoutsOverviewOut:
    payouts = await svc.list_payouts(session, user.id)
    return PayoutsOverviewOut(
        payouts=[PayoutOut.model_validate(p) for p in payouts],
        summary=PayoutsSummaryOut(**svc.payouts_summary(payouts)),
    )


@router.post("/payouts", response_model=PayoutOut, status_code=status.HTTP_201_CREATED)
async def add_payout(
    payload: PayoutIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PayoutOut:
    if payload.type not in svc.PAYOUT_TYPES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Тип должен быть одним из: {', '.join(svc.PAYOUT_TYPES)}",
        )
    if payload.product_id is not None:
        product = await products_svc.get_user_product(
            session, user.id, payload.product_id
        )
        if product is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    payout = Payout(
        user_id=user.id,
        product_id=payload.product_id,
        type=payload.type,
        amount=payload.amount,
        note=payload.note,
    )
    session.add(payout)
    await session.commit()
    await session.refresh(payout)
    return PayoutOut.model_validate(payout)


@router.delete("/payouts/{payout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payout(
    payout_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    payout = await session.get(Payout, payout_id)
    if payout is None or payout.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Запись не найдена")
    await session.delete(payout)
    await session.commit()


@router.get("/products/{product_id}/pnl", response_model=PnLOut)
async def get_pnl(
    product_id: int,
    units: int = Query(1, ge=0, description="Количество проданных единиц"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PnLOut:
    """Отчёт о прибылях и убытках по товару (P&L)."""
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    params = await pricing_svc.economics_params(session, product_id)
    result = await svc.compute_pnl(session, product, params, units)
    return PnLOut(
        units=result.units,
        revenue=result.revenue,
        cost_of_goods=result.cost_of_goods,
        marketplace_costs=result.marketplace_costs,
        ad_costs=result.ad_costs,
        adjustments=result.adjustments,
        total_costs=result.total_costs,
        net_profit=result.net_profit,
        margin_pct=result.margin_pct,
    )
