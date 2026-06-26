"""Склад и поставки: прогноз остатка, рекомендация по отгрузке, статусы.

Скорость продаж (шт/день) задаёт продавец — реальных данных о продажах
парсинг не даёт, поэтому прогноз честно строится от введённой скорости.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product


@dataclass
class WarehouseParams:
    daily_sales: float = 0.0
    lead_time_days: int = 14
    target_cover_days: int = 30
    low_stock_threshold_days: int = 7


@dataclass
class WarehouseForecast:
    stock: int
    daily_sales: float
    days_left: int | None
    recommended_supply: int
    status: str  # out | critical | low | ok | unknown
    params: WarehouseParams


def compute_forecast(stock: int | None, params: WarehouseParams) -> WarehouseForecast:
    stock = int(stock or 0)
    ds = float(params.daily_sales or 0.0)

    days_left: int | None = None
    recommended = 0
    if ds > 0:
        days_left = math.floor(stock / ds)
        # запас под время поставки + целевое покрытие
        target_units = ds * (params.lead_time_days + params.target_cover_days)
        recommended = max(0, math.ceil(target_units - stock))

    if stock <= 0:
        status = "out"
    elif ds <= 0:
        status = "unknown"
    elif days_left is not None and days_left <= params.lead_time_days:
        status = "critical"
    elif days_left is not None and days_left <= params.low_stock_threshold_days:
        status = "low"
    else:
        status = "ok"

    return WarehouseForecast(
        stock=stock,
        daily_sales=ds,
        days_left=days_left,
        recommended_supply=recommended,
        status=status,
        params=params,
    )


def params_from_product(product: Product) -> WarehouseParams:
    return WarehouseParams(
        daily_sales=float(product.daily_sales or 0.0),
        lead_time_days=product.lead_time_days,
        target_cover_days=product.target_cover_days,
        low_stock_threshold_days=product.low_stock_threshold_days,
    )


def forecast_for_product(product: Product) -> WarehouseForecast:
    return compute_forecast(product.stock, params_from_product(product))


async def save_params(
    session: AsyncSession, product: Product, params: WarehouseParams
) -> WarehouseForecast:
    product.daily_sales = params.daily_sales
    product.lead_time_days = params.lead_time_days
    product.target_cover_days = params.target_cover_days
    product.low_stock_threshold_days = params.low_stock_threshold_days
    await session.commit()
    return compute_forecast(product.stock, params)
