from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AdStatIn(BaseModel):
    label: str = Field(..., min_length=1, max_length=128)
    spend: float = Field(..., ge=0)
    revenue: float = Field(0, ge=0)
    clicks: int = Field(0, ge=0)
    orders: int = Field(0, ge=0)


class AdStatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    spend: float
    revenue: float
    clicks: int | None = None
    orders: int | None = None
    created_at: datetime


class AdMetricsOut(BaseModel):
    spend: float
    revenue: float
    clicks: int
    orders: int
    drr: float | None = None
    roi: float | None = None
    cpo: float | None = None
    cpc: float | None = None
    recommendation: str


class AdOverviewOut(BaseModel):
    stats: list[AdStatOut]
    total: AdMetricsOut
