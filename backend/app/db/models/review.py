from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Review(Base, TimestampMixin):
    """Отзыв (мой или конкурента). Источник — маркетплейс."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Привязка либо к моему товару, либо к конкуренту (одна из ссылок заполнена)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=True
    )
    competitor_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"), index=True, nullable=True
    )

    # Идентификатор отзыва на площадке (для дедупликации при проверке новых)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)

    source: Mapped[str] = mapped_column(String(32), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Тональность: 'positive' | 'neutral' | 'negative' (заполняется на Этапе 10)
    sentiment: Mapped[str | None] = mapped_column(String(16), nullable=True)
