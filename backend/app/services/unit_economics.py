"""Юнит-экономика: расчёт чистой прибыли по товару.

Чистая функция расчёта (без БД) + сохранение параметров и результата в
таблицу unit_economics (одна запись на товар).

Модель затрат на единицу:
  выручка        = цена продажи
  комиссия       = цена * commission_pct%
  эквайринг      = цена * acquiring_pct%
  налог          = цена * tax_pct%        (УСН с оборота; ставку задаёт продавец)
  возвраты       = цена * returns_pct%    (доля на реверс-логистику/потери)
  логистика      = logistics_cost ₽       (абсолютная, за единицу)
  хранение       = storage_cost ₽         (абсолютная, за единицу)
  себестоимость  = cost_price ₽
  прибыль        = выручка - сумма затрат
  маржа, %       = прибыль / выручка * 100
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product, UnitEconomics


@dataclass
class EconomicsParams:
    commission_pct: float = 0.0
    logistics_cost: float = 0.0
    storage_cost: float = 0.0
    acquiring_pct: float = 0.0
    returns_pct: float = 0.0
    tax_pct: float = 0.0


@dataclass
class EconomicsResult:
    price: float
    cost_price: float
    breakdown: dict[str, float] = field(default_factory=dict)
    total_costs: float = 0.0
    net_profit: float = 0.0
    margin_pct: float | None = None
    is_profitable: bool = False


def _pct(base: float, pct: float) -> float:
    return round(base * (pct or 0.0) / 100.0, 2)


def compute_economics(
    price: float | None, cost_price: float | None, params: EconomicsParams
) -> EconomicsResult:
    """Считает разбивку затрат и чистую прибыль на единицу."""
    price = float(price or 0.0)
    cost_price = float(cost_price or 0.0)

    commission = _pct(price, params.commission_pct)
    acquiring = _pct(price, params.acquiring_pct)
    tax = _pct(price, params.tax_pct)
    returns = _pct(price, params.returns_pct)
    logistics = round(float(params.logistics_cost or 0.0), 2)
    storage = round(float(params.storage_cost or 0.0), 2)

    breakdown = {
        "cost_price": round(cost_price, 2),
        "commission": commission,
        "acquiring": acquiring,
        "tax": tax,
        "returns": returns,
        "logistics": logistics,
        "storage": storage,
    }
    total_costs = round(sum(breakdown.values()), 2)
    net_profit = round(price - total_costs, 2)
    margin_pct = round(net_profit / price * 100, 2) if price else None

    return EconomicsResult(
        price=round(price, 2),
        cost_price=round(cost_price, 2),
        breakdown=breakdown,
        total_costs=total_costs,
        net_profit=net_profit,
        margin_pct=margin_pct,
        is_profitable=net_profit > 0,
    )


async def get_or_default(
    session: AsyncSession, product_id: int
) -> UnitEconomics | None:
    result = await session.execute(
        select(UnitEconomics).where(UnitEconomics.product_id == product_id)
    )
    return result.scalar_one_or_none()


async def save_and_compute(
    session: AsyncSession, product: Product, params: EconomicsParams
) -> EconomicsResult:
    """Сохраняет параметры (upsert) и считает результат по текущей цене товара."""
    result = compute_economics(
        float(product.price) if product.price is not None else None,
        float(product.cost_price) if product.cost_price is not None else None,
        params,
    )

    row = await get_or_default(session, product.id)
    if row is None:
        row = UnitEconomics(product_id=product.id)
        session.add(row)

    row.commission_pct = params.commission_pct
    row.logistics_cost = params.logistics_cost
    row.storage_cost = params.storage_cost
    row.acquiring_pct = params.acquiring_pct
    row.returns_pct = params.returns_pct
    row.tax_pct = params.tax_pct
    row.net_profit = result.net_profit
    row.margin_pct = result.margin_pct

    await session.commit()
    return result
