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
    registered_at: datetime


class AuthResponse(BaseModel):
    user: UserOut
    is_new: bool
