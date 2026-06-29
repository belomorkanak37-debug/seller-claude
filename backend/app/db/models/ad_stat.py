from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AdStat(Base):
    """Рекламная статистика по товару за период (вводит продавец)."""

    __tablename__ = "ad_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str] = mapped_column(String(128), nullable=False)  # период/кампания
    spend: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    revenue: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    clicks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    orders: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
