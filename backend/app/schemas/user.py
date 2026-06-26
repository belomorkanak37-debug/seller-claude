from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuthRequest(BaseModel):
    """Тело запроса авторизации Mini App: сырой initData от Telegram."""

    init_data: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    photo_url: str | None = None
    notifications_enabled: bool
    notify_new_reviews: bool
    notify_stock: bool
    registered_at: datetime


class AuthResponse(BaseModel):
    user: UserOut
    is_new: bool


class UserSettingsUpdate(BaseModel):
    notifications_enabled: bool | None = None
    notify_new_reviews: bool | None = None
    notify_stock: bool | None = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str | None = None
    body: str | None = None
    sent_at: datetime
