"""Отправка уведомлений в Telegram и лог в БД.

Бэкенд/воркер шлёт сообщение через Bot API напрямую (httpx) и пишет запись в
таблицу notifications. Так уведомления не зависят от того, поднят ли поллинг
бота именно сейчас.
"""

from __future__ import annotations

import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Notification, Product, Review, User

logger = logging.getLogger(__name__)


async def send_telegram_message(chat_id: int, text: str) -> bool:
    """Отправляет сообщение пользователю. Возвращает True при успехе."""
    if not settings.bot_token:
        logger.warning("BOT_TOKEN не задан — уведомление не отправлено")
        return False
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
        if resp.status_code != 200:
            logger.warning("sendMessage %s: %s", resp.status_code, resp.text)
            return False
        return True
    except httpx.HTTPError as exc:
        logger.warning("sendMessage error: %s", exc)
        return False


async def log_notification(
    session: AsyncSession,
    user_id: int,
    type_: str,
    title: str | None,
    body: str | None,
) -> Notification:
    notification = Notification(
        user_id=user_id, type=type_, title=title, body=body
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification


def _format_new_reviews(product: Product, new_reviews: list[Review]) -> str:
    count = len(new_reviews)
    word = "новый отзыв" if count == 1 else "новых отзыва(ов)"
    lines = [f"🔔 По товару <b>{product.name}</b> — {count} {word}:"]
    for r in new_reviews[:3]:
        stars = "⭐" * int(r.rating) if r.rating else ""
        text = (r.text or "").strip().replace("\n", " ")
        if len(text) > 120:
            text = text[:120] + "…"
        lines.append(f"\n{stars} {text}" if text else f"\n{stars}")
    if count > 3:
        lines.append(f"\n…и ещё {count - 3}")
    return "".join(lines)


async def notify_new_reviews(
    session: AsyncSession,
    user: User,
    product: Product,
    new_reviews: list[Review],
) -> bool:
    """Шлёт уведомление о новых отзывах с учётом настроек пользователя."""
    if not new_reviews:
        return False
    if not user.notifications_enabled or not user.notify_new_reviews:
        return False

    text = _format_new_reviews(product, new_reviews)
    sent = await send_telegram_message(user.telegram_id, text)
    if sent:
        await log_notification(
            session,
            user.id,
            type_="new_review",
            title=f"Новые отзывы: {product.name}"[:512],
            body=text,
        )
    return sent
