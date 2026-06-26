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


class Competitor(Base, TimestampMixin):
    """Конкурент, привязанный к товару продавца."""

    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )

    marketplace: Mapped[str] = mapped_column(String(32), nullable=False)
    article: Mapped[str | None] = mapped_column(String(128), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    name: Mapped[str] = mapped_column(String(1024), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Заметка продавца (вместо «добавить отзыв»)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(  # noqa: F821
        back_populates="competitors"
    )
