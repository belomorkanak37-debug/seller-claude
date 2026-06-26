from datetime import datetime

from sqlalchemy import BigInteger, Boolean, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # telegram_id уникален и приходит из проверенного initData
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Настройки уведомлений: мастер-выключатель + по типам
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    notify_new_reviews: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    notify_stock: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    registered_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    products: Mapped[list["Product"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
