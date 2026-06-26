from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PriceSnapshot(Base):
    """Снимок цены по расписанию. Из накопленных снапшотов строим график."""

    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=True
    )
    competitor_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"), index=True, nullable=True
    )

    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), index=True, nullable=False
    )
