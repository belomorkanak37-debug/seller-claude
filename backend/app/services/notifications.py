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
from app.db.models import Competitor, Notification, Product, Review, User

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


async def notify_low_stock(
    session: AsyncSession, user: User, product: Product, forecast
) -> bool:
    """Алерт о низком/нулевом остатке с рекомендацией по отгрузке."""
    if not user.notifications_enabled or not user.notify_stock:
        return False
    if forecast.status not in ("low", "critical", "out"):
        return False

    if forecast.status == "out":
        head = f"⛔️ Товар <b>{product.name}</b> закончился на складе"
    else:
        days = forecast.days_left
        head = (
            f"📦 Низкий остаток по <b>{product.name}</b>: "
            f"{forecast.stock} шт (хватит на ~{days} дн.)"
        )
    body = head
    if forecast.recommended_supply > 0:
        body += f"\nРекомендуем отгрузить: {forecast.recommended_supply} шт"

    sent = await send_telegram_message(user.telegram_id, body)
    if sent:
        await log_notification(
            session, user.id, "low_stock", f"Остаток: {product.name}"[:512], body
        )
    return sent


async def notify_competitor_oos(
    session: AsyncSession, user: User, product: Product, competitor: Competitor
) -> bool:
    """Триггер: конкурент ушёл в out-of-stock — можно поднять цену."""
    if not user.notifications_enabled or not user.notify_stock:
        return False
    body = (
        f"📈 Конкурент <b>{competitor.name}</b> закончился (out-of-stock).\n"
        f"По товару <b>{product.name}</b> можно поднять цену."
    )
    sent = await send_telegram_message(user.telegram_id, body)
    if sent:
        await log_notification(
            session,
            user.id,
            "competitor_oos",
            f"Конкурент OOS: {product.name}"[:512],
            body,
        )
    return sent
