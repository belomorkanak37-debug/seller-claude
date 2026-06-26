import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.config import settings
from app.handlers import start

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN не задан в .env")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(start.router)

    # Кнопка-меню рядом с полем ввода тоже открывает Mini App.
    if settings.webapp_url:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Открыть",
                web_app=WebAppInfo(url=settings.webapp_url),
            )
        )

    # Polling-режим: снимаем возможный webhook и забираем накопленные апдейты.
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started in polling mode")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
