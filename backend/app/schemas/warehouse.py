from pydantic import BaseModel, Field


class WarehouseParamsIn(BaseModel):
    daily_sales: float = Field(0, ge=0)
    lead_time_days: int = Field(14, ge=0)
    target_cover_days: int = Field(30, ge=0)
    low_stock_threshold_days: int = Field(7, ge=0)


class WarehouseForecastOut(BaseModel):
    stock: int
    daily_sales: float
    days_left: int | None = None
    recommended_supply: int
    status: str
    params: WarehouseParamsIn
