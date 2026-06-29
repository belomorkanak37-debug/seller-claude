from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import AdStat, Product, User
from app.db.session import get_session
from app.schemas.advertising import (
    AdMetricsOut,
    AdOverviewOut,
    AdStatIn,
    AdStatOut,
)
from app.services import advertising as svc
from app.services import products as products_svc

router = APIRouter(tags=["advertising"])


def _metrics_out(m) -> AdMetricsOut:
    return AdMetricsOut(
        spend=m.spend, revenue=m.revenue, clicks=m.clicks, orders=m.orders,
        drr=m.drr, roi=m.roi, cpo=m.cpo, cpc=m.cpc, recommendation=m.recommendation,
    )


@router.get("/products/{product_id}/ads", response_model=AdOverviewOut)
async def get_ads(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AdOverviewOut:
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    stats = await svc.list_ad_stats(session, product_id)
    total = await svc.aggregate_ad_metrics(session, product_id)
    return AdOverviewOut(
        stats=[AdStatOut.model_validate(s) for s in stats],
        total=_metrics_out(total),
    )


@router.post(
    "/products/{product_id}/ads",
    response_model=AdStatOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_ad_stat(
    product_id: int,
    payload: AdStatIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AdStatOut:
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    stat = AdStat(
        product_id=product_id,
        label=payload.label,
        spend=payload.spend,
        revenue=payload.revenue,
        clicks=payload.clicks,
        orders=payload.orders,
    )
    session.add(stat)
    await session.commit()
    await session.refresh(stat)
    return AdStatOut.model_validate(stat)


@router.delete("/ads/{stat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad_stat(
    stat_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    stat = await session.get(AdStat, stat_id)
    if stat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Запись не найдена")
    product = await products_svc.get_user_product(session, user.id, stat.product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Запись не найдена")
    await session.delete(stat)
    await session.commit()
