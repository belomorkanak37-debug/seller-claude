"""Ценообразование: авто-репрайсер, контроль минимальной цены, промо-калькулятор.

Применять новую цену на маркетплейс автоматически нельзя из read-only слоя
парсинга — это требует write-API кабинета продавца. Поэтому здесь считаются
рекомендации по правилам, а продавец применяет их в кабинете.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Competitor, Product, UnitEconomics
from app.services.unit_economics import EconomicsParams, compute_economics


@dataclass
class RepriceRule:
    enabled: bool = False
    undercut_pct: float = 0.0
    min_price: float | None = None
    max_price: float | None = None


@dataclass
class RepriceResult:
    current_price: float | None
    lowest_competitor: float | None
    target_price: float | None
    recommended_price: float | None
    floor: float | None
    floor_hit: bool
    would_change: bool
    direction: str  # down | up | none
    reason: str


def compute_reprice(
    current_price: float | None,
    competitor_prices: list[float],
    rule: RepriceRule,
) -> RepriceResult:
    prices = [p for p in competitor_prices if p and p > 0]
    lowest = min(prices) if prices else None
    floor = rule.min_price

    if lowest is None:
        return RepriceResult(
            current_price=current_price,
            lowest_competitor=None,
            target_price=None,
            recommended_price=current_price,
            floor=floor,
            floor_hit=False,
            would_change=False,
            direction="none",
            reason="Нет цен конкурентов для сравнения",
        )

    target = round(lowest * (1 - (rule.undercut_pct or 0) / 100))
    recommended = target
    floor_hit = False
    reason = f"На {rule.undercut_pct or 0}% ниже минимальной цены конкурента"

    if floor is not None and recommended < floor:
        recommended = round(floor)
        floor_hit = True
        reason = "Достигнута минимальная цена — не демпингуем ниже"
    if rule.max_price is not None and recommended > rule.max_price:
        recommended = round(rule.max_price)
        reason = "Ограничено максимальной ценой"

    cur = round(current_price) if current_price is not None else None
    would_change = cur is None or cur != recommended
    if cur is None:
        direction = "none"
    elif recommended < cur:
        direction = "down"
    elif recommended > cur:
        direction = "up"
    else:
        direction = "none"

    return RepriceResult(
        current_price=current_price,
        lowest_competitor=lowest,
        target_price=float(target),
        recommended_price=float(recommended),
        floor=floor,
        floor_hit=floor_hit,
        would_change=would_change,
        direction=direction,
        reason=reason,
    )


def break_even_price(cost_price: float, params: EconomicsParams) -> float | None:
    """Цена безубыточности с учётом комиссии/налога/логистики/хранения."""
    k = (
        (params.commission_pct or 0)
        + (params.acquiring_pct or 0)
        + (params.tax_pct or 0)
        + (params.returns_pct or 0)
    ) / 100.0
    denom = 1 - k
    if denom <= 0:
        return None
    fixed = (cost_price or 0) + (params.logistics_cost or 0) + (params.storage_cost or 0)
    return round(fixed / denom, 2)


@dataclass
class PromoResult:
    base_price: float
    promo_price: float
    discount_pct: float
    net_profit: float
    margin_pct: float | None
    is_profitable: bool
    profit_delta: float  # промо-прибыль минус базовая


def compute_promo(
    base_price: float,
    cost_price: float,
    params: EconomicsParams,
    *,
    promo_price: float | None = None,
    discount_pct: float | None = None,
) -> PromoResult:
    base_price = float(base_price or 0)
    if promo_price is None:
        discount_pct = float(discount_pct or 0)
        promo_price = round(base_price * (1 - discount_pct / 100), 2)
    else:
        promo_price = float(promo_price)
        discount_pct = (
            round((1 - promo_price / base_price) * 100, 2) if base_price else 0.0
        )

    base_econ = compute_economics(base_price, cost_price, params)
    promo_econ = compute_economics(promo_price, cost_price, params)

    return PromoResult(
        base_price=round(base_price, 2),
        promo_price=promo_price,
        discount_pct=discount_pct,
        net_profit=promo_econ.net_profit,
        margin_pct=promo_econ.margin_pct,
        is_profitable=promo_econ.is_profitable,
        profit_delta=round(promo_econ.net_profit - base_econ.net_profit, 2),
    )


# ── helpers для работы с БД ───────────────────────────────────


async def competitor_prices(session: AsyncSession, product_id: int) -> list[float]:
    rows = await session.execute(
        select(Competitor.price).where(Competitor.product_id == product_id)
    )
    return [float(p) for (p,) in rows.all() if p is not None]


async def economics_params(
    session: AsyncSession, product_id: int
) -> EconomicsParams:
    row = (
        await session.execute(
            select(UnitEconomics).where(UnitEconomics.product_id == product_id)
        )
    ).scalar_one_or_none()
    if row is None:
        return EconomicsParams()
    return EconomicsParams(
        commission_pct=float(row.commission_pct or 0),
        logistics_cost=float(row.logistics_cost or 0),
        storage_cost=float(row.storage_cost or 0),
        acquiring_pct=float(row.acquiring_pct or 0),
        returns_pct=float(row.returns_pct or 0),
        tax_pct=float(row.tax_pct or 0),
    )


def rule_from_product(product: Product) -> RepriceRule:
    return RepriceRule(
        enabled=product.repricer_enabled,
        undercut_pct=float(product.undercut_pct or 0),
        min_price=float(product.min_price) if product.min_price is not None else None,
        max_price=float(product.max_price) if product.max_price is not None else None,
    )


async def save_rule(
    session: AsyncSession, product: Product, rule: RepriceRule
) -> None:
    product.repricer_enabled = rule.enabled
    product.undercut_pct = rule.undercut_pct
    product.min_price = rule.min_price
    product.max_price = rule.max_price
    await session.commit()
