from sqlalchemy import (
    JSON,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    """Товар продавца. Поля редактируемые после добавления."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # marketplace: 'ozon' | 'wildberries' | 'yandex_market'
    marketplace: Mapped[str] = mapped_column(String(32), nullable=False)
    article: Mapped[str] = mapped_column(String(128), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(1024), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Теги/характеристики карточки
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    stock: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Параметры для юнит-экономики (заполняются продавцом)
    cost_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="products")  # noqa: F821
    competitors: Mapped[list["Competitor"]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan"
    )
