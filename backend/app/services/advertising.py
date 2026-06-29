"""Аналитика рекламы: ДРР, ROI, CPO, рекомендация по ставкам."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdStat


@dataclass
class AdMetrics:
    spend: float
    revenue: float
    clicks: int
    orders: int
    drr: float | None       # доля рекламных расходов, % (spend/revenue)
    roi: float | None       # рентабельность, % ((revenue-spend)/spend)
    cpo: float | None       # стоимость заказа (spend/orders)
    cpc: float | None       # цена клика (spend/clicks)
    recommendation: str


def compute_ad_metrics(
    spend: float, revenue: float, clicks: int = 0, orders: int = 0
) -> AdMetrics:
    spend = float(spend or 0)
    revenue = float(revenue or 0)
    clicks = int(clicks or 0)
    orders = int(orders or 0)

    drr = round(spend / revenue * 100, 2) if revenue else None
    roi = round((revenue - spend) / spend * 100, 2) if spend else None
    cpo = round(spend / orders, 2) if orders else None
    cpc = round(spend / clicks, 2) if clicks else None

    if drr is None:
        rec = "Недостаточно данных: укажите выручку с рекламы."
    elif drr > 25:
        rec = f"ДРР {drr}% высок — снизьте ставки или уточните ключевые слова."
    elif drr > 15:
        rec = f"ДРР {drr}% в норме — точечно оптимизируйте неэффективные запросы."
    else:
        rec = f"ДРР {drr}% низкий — есть запас, можно поднять ставки для роста."

    return AdMetrics(
        spend=round(spend, 2),
        revenue=round(revenue, 2),
        clicks=clicks,
        orders=orders,
        drr=drr,
        roi=roi,
        cpo=cpo,
        cpc=cpc,
        recommendation=rec,
    )


async def list_ad_stats(session: AsyncSession, product_id: int) -> list[AdStat]:
    rows = await session.execute(
        select(AdStat)
        .where(AdStat.product_id == product_id)
        .order_by(AdStat.created_at.desc())
    )
    return list(rows.scalars().all())


async def aggregate_ad_metrics(
    session: AsyncSession, product_id: int
) -> AdMetrics:
    stats = await list_ad_stats(session, product_id)
    return compute_ad_metrics(
        spend=sum(float(s.spend) for s in stats),
        revenue=sum(float(s.revenue) for s in stats),
        clicks=sum(int(s.clicks or 0) for s in stats),
        orders=sum(int(s.orders or 0) for s in stats),
    )
