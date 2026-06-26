from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.telegram_auth import InitDataError, validate_init_data
from app.db.models import User
from app.db.session import get_session
from app.schemas.user import AuthRequest, AuthResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=AuthResponse)
async def auth_telegram(
    payload: AuthRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    """Валидирует initData и создаёт/находит пользователя по telegram_id."""
    try:
        parsed = validate_init_data(
            payload.init_data,
            settings.bot_token,
            settings.initdata_max_age_seconds,
        )
    except InitDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Невалидный initData: {exc}",
        ) from exc

    tg = parsed.user
    result = await session.execute(
        select(User).where(User.telegram_id == tg.id)
    )
    user = result.scalar_one_or_none()
    is_new = False

    if user is None:
        user = User(
            telegram_id=tg.id,
            username=tg.username,
            first_name=tg.first_name,
            last_name=tg.last_name,
            language_code=tg.language_code,
            photo_url=tg.photo_url,
        )
        session.add(user)
        is_new = True
    else:
        # Обновляем профиль на случай изменений в Telegram
        user.username = tg.username
        user.first_name = tg.first_name
        user.last_name = tg.last_name
        user.language_code = tg.language_code
        user.photo_url = tg.photo_url

    await session.commit()
    await session.refresh(user)

    return AuthResponse(user=UserOut.model_validate(user), is_new=is_new)
