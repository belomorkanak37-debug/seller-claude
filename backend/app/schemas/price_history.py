from datetime import datetime

from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    captured_at: datetime
    price: float


class PriceSeries(BaseModel):
    label: str
    competitor_id: int | None = None
    points: list[PricePoint] = Field(default_factory=list)


class PriceHistoryOut(BaseModel):
    product: PriceSeries
    competitors: list[PriceSeries] = Field(default_factory=list)


class SnapshotResult(BaseModel):
    product: int
    competitors: int
