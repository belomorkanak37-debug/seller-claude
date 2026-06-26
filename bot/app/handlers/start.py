from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app.config import settings

router = Router()


def _webapp_keyboard() -> InlineKeyboardMarkup:
    """Кнопка, открывающая Mini App в WebView Telegram."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Открыть приложение",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ]
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    name = message.from_user.first_name if message.from_user else "продавец"
    text = (
        f"Привет, {name}! 👋\n\n"
        "Это помощник продавца на маркетплейсах Ozon, Wildberries и "
        "Яндекс Маркет.\n\n"
        "Добавляй свои товары по артикулу, следи за конкурентами, ценами, "
        "отзывами и аналитикой.\n\n"
        "Нажми кнопку ниже, чтобы открыть приложение 👇"
    )
    if not settings.webapp_url:
        await message.answer(
            "⚠️ WEBAPP_URL не сконфигурирован. Задай его в .env "
            "(публичный HTTPS-адрес Mini App)."
        )
        return
    await message.answer(text, reply_markup=_webapp_keyboard())
