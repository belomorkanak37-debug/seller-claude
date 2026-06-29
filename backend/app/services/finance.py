"""Финансы: сверка выплат маркетплейса и P&L по товару."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdStat, Payout, Product
from app.services.unit_economics import EconomicsParams, compute_economics

PAYOUT_TYPES = ("payout", "fine", "withholding", "correction")


# ── Сверка выплат ─────────────────────────────────────────────


async def list_payouts(session: AsyncSession, user_id: int) -> list[Payout]:
    rows = await session.execute(
        select(Payout)
        .where(Payout.user_id == user_id)
        .order_by(Payout.occurred_at.desc())
    )
    return list(rows.scalars().all())


def payouts_summary(payouts: list[Payout]) -> dict:
    totals = {t: 0.0 for t in PAYOUT_TYPES}
    for p in payouts:
        if p.type in totals:
            totals[p.type] += float(p.amount)
    totals = {k: round(v, 2) for k, v in totals.items()}
    # Чистыми на руки: выплаты + корректировки − штрафы − удержания
    net = round(
        totals["payout"]
        + totals["correction"]
        - totals["fine"]
        - totals["withholding"],
        2,
    )
    return {**totals, "net": net}


# ── P&L по товару ─────────────────────────────────────────────


@dataclass
class PnLResult:
    units: int
    revenue: float
    cost_of_goods: float
    marketplace_costs: float
    ad_costs: float
    adjustments: float
    total_costs: float
    net_profit: float
    margin_pct: float | None


async def compute_pnl(
    session: AsyncSession,
    product: Product,
    params: EconomicsParams,
    units: int,
) -> PnLResult:
    units = max(0, int(units))
    price = float(product.price or 0)
    cost_price = float(product.cost_price or 0)

    econ = compute_economics(price, cost_price, params)
    cost_of_goods = round(econ.breakdown["cost_price"] * units, 2)
    marketplace_costs = round(
        (econ.total_costs - econ.breakdown["cost_price"]) * units, 2
    )

    ad_spend = (
        await session.execute(
            select(AdStat.spend).where(AdStat.product_id == product.id)
        )
    ).scalars().all()
    ad_costs = round(sum(float(s) for s in ad_spend), 2)

    payouts = await list_payouts(session, product.user_id)
    # Корректировки/штрафы по этому товару влияют на его P&L
    adj = 0.0
    for p in payouts:
        if p.product_id != product.id:
            continue
        if p.type == "correction":
            adj += float(p.amount)
        elif p.type in ("fine", "withholding"):
            adj -= float(p.amount)
    adjustments = round(adj, 2)

    revenue = round(price * units, 2)
    total_costs = round(cost_of_goods + marketplace_costs + ad_costs, 2)
    net_profit = round(revenue - total_costs + adjustments, 2)
    margin = round(net_profit / revenue * 100, 2) if revenue else None

    return PnLResult(
        units=units,
        revenue=revenue,
        cost_of_goods=cost_of_goods,
        marketplace_costs=marketplace_costs,
        ad_costs=ad_costs,
        adjustments=adjustments,
        total_costs=total_costs,
        net_profit=net_profit,
        margin_pct=margin,
    )
