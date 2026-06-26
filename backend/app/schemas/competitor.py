from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompetitorPreview(BaseModel):
    """Карточка конкурента из поиска (ещё не сохранена)."""

    marketplace: str
    article: str | None = None
    name: str
    price: float | None = None
    photo_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    url: str | None = None


class CompetitorSearchResponse(BaseModel):
    keywords: list[str]
    competitors: list[CompetitorPreview] = Field(default_factory=list)


class CompetitorCreate(BaseModel):
    """Добавление выбранного конкурента (из результатов поиска)."""

    marketplace: str
    article: str | None = None
    url: str | None = None
    name: str
    price: float | None = None
    photo_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    note: str | None = None


class CompetitorUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    rating: float | None = None
    reviews_count: int | None = None
    photo_url: str | None = None
    tags: list[str] | None = None
    note: str | None = None


class CompetitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    marketplace: str
    article: str | None = None
    url: str | None = None
    name: str
    photo_url: str | None = None
    price: float | None = None
    rating: float | None = None
    reviews_count: int | None = None
    tags: list[str] | None = None
    note: str | None = None
    created_at: datetime
    updated_at: datetime
