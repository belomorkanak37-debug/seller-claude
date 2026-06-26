from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PositionSnapshot(Base):
    """Позиция товара в поиске по запросу на момент снятия (Этап 9)."""

    __tablename__ = "position_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    query: Mapped[str] = mapped_column(String(512), nullable=False)
    # None = товар не найден в первых N результатах
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), index=True, nullable=False
    )
