"""Зависимости FastAPI: авторизация по initData для защищённых эндпоинтов.

Mini App на каждый запрос к защищённому API передаёт заголовок
`Authorization: tma <initData>`. Здесь мы валидируем подпись и находим
пользователя. Так логика «верим только проверенной подписи» соблюдается
на всех маршрутах, не только при логине.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.telegram_auth import InitDataError, validate_init_data
from app.db.models import User
from app.db.session import get_session


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not authorization or not authorization.lower().startswith("tma "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутствует заголовок Authorization: tma <initData>",
        )

    init_data = authorization[4:].strip()
    try:
        parsed = validate_init_data(
            init_data,
            settings.bot_token,
            settings.initdata_max_age_seconds,
        )
    except InitDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Невалидный initData: {exc}",
        ) from exc

    result = await session.execute(
        select(User).where(User.telegram_id == parsed.user.id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден. Выполните /auth/telegram.",
        )
    return user
