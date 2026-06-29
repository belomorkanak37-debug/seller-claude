from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PayoutIn(BaseModel):
    type: str = Field(..., description="payout | fine | withholding | correction")
    amount: float = Field(..., ge=0)
    product_id: int | None = None
    note: str | None = None


class PayoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    amount: float
    product_id: int | None = None
    note: str | None = None
    occurred_at: datetime


class PayoutsSummaryOut(BaseModel):
    payout: float = 0
    fine: float = 0
    withholding: float = 0
    correction: float = 0
    net: float = 0


class PayoutsOverviewOut(BaseModel):
    payouts: list[PayoutOut]
    summary: PayoutsSummaryOut


class PnLOut(BaseModel):
    units: int
    revenue: float
    cost_of_goods: float
    marketplace_costs: float
    ad_costs: float
    adjustments: float
    total_costs: float
    net_profit: float
    margin_pct: float | None = None
