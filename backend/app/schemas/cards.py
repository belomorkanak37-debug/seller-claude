from datetime import datetime

from pydantic import BaseModel, Field


class PositionItem(BaseModel):
    query: str
    position: int | None = None


class PositionPoint(BaseModel):
    captured_at: datetime
    position: int | None = None


class PositionSeries(BaseModel):
    query: str
    points: list[PositionPoint] = Field(default_factory=list)


class PositionsOut(BaseModel):
    queries: list[str]
    latest: list[PositionItem] = Field(default_factory=list)
    history: list[PositionSeries] = Field(default_factory=list)


class TrackedQueriesIn(BaseModel):
    queries: list[str] = Field(default_factory=list)


class CardMetricsOut(BaseModel):
    has_photo: bool
    rating: float
    reviews_count: int
    tags_count: int
    price: float | None = None
    name_length: int


class CardComparisonOut(BaseModel):
    product: CardMetricsOut
    competitors_avg: dict
    recommendations: list[str]


class SeoOut(BaseModel):
    suggested_keywords: list[str]
    score: int
    tips: list[str]
