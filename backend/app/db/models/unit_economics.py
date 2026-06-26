from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UnitEconomics(Base, TimestampMixin):
    """Параметры и результат расчёта юнит-экономики по товару (Этап 6)."""

    __tablename__ = "unit_economics"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Все ставки/суммы — входные параметры расчёта
    commission_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    logistics_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    storage_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    acquiring_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    returns_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    tax_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)

    # Результат расчёта
    net_profit: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    margin_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
