from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.review import ReviewOut


class ProductPreview(BaseModel):
    """Живые данные карточки для экрана «Это ваш товар?» (ещё не сохранено)."""

    marketplace: str
    article: str
    name: str
    price: float | None = None
    photo_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    tags: list[str] = Field(default_factory=list)
    stock: int | None = None
    url: str | None = None
    brand: str | None = None
    reviews: list[ReviewOut] = Field(default_factory=list)


class ProductCreate(BaseModel):
    """Подтверждение товара. Сервер заново тянет реальные данные по артикулу."""

    marketplace: str
    article: str
    # Необязательная себестоимость для будущей юнит-экономики
    cost_price: float | None = None


class ProductUpdate(BaseModel):
    """Редактирование товара — любые поля опциональны."""

    name: str | None = None
    price: float | None = None
    photo_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    tags: list[str] | None = None
    stock: int | None = None
    cost_price: float | None = None
    notes: str | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    marketplace: str
    article: str
    name: str
    price: float | None = None
    photo_url: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    tags: list[str] | None = None
    stock: int | None = None
    cost_price: float | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
