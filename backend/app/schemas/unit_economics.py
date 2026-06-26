from pydantic import BaseModel, Field


class EconomicsParamsIn(BaseModel):
    commission_pct: float = Field(0, ge=0)
    logistics_cost: float = Field(0, ge=0)
    storage_cost: float = Field(0, ge=0)
    acquiring_pct: float = Field(0, ge=0)
    returns_pct: float = Field(0, ge=0)
    tax_pct: float = Field(0, ge=0)


class EconomicsOut(BaseModel):
    price: float
    cost_price: float
    params: EconomicsParamsIn
    breakdown: dict[str, float]
    total_costs: float
    net_profit: float
    margin_pct: float | None = None
    is_profitable: bool
