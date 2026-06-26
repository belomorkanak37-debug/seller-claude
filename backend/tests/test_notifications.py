"""Этап 4: сервис уведомлений — гейтинг по настройкам и лог."""

import pytest
from sqlalchemy import select

from app.db.models import Notification, Product, Review, User
from app.services import notifications as notify_svc


@pytest.mark.asyncio
async def test_notify_respects_settings_and_logs(db, monkeypatch):
    sent: list[tuple[int, str]] = []

    async def fake_send(chat_id, text):
        sent.append((chat_id, text))
        return True

    monkeypatch.setattr(notify_svc, "send_telegram_message", fake_send)

    async with db() as session:
        user = (await session.execute(select(User))).scalars().first()
        product = Product(
            user_id=user.id, marketplace="wildberries", article="123",
            name="Комод белый",
        )
        session.add(product)
        await session.flush()
        review = Review(
            product_id=product.id, external_id="r2", source="wildberries",
            author="Борис", text="супер товар", rating=5,
        )
        session.add(review)
        await session.commit()
        await session.refresh(review)

        # 1) Включено — уведомление уходит и логируется
        ok = await notify_svc.notify_new_reviews(session, user, product, [review])
        assert ok is True
        assert len(sent) == 1
        assert sent[0][0] == user.telegram_id
        logs = (await session.execute(select(Notification))).scalars().all()
        assert len(logs) == 1
        assert logs[0].type == "new_review"

        # 2) Выключен тип уведомления — не уходит
        user.notify_new_reviews = False
        await session.commit()
        ok = await notify_svc.notify_new_reviews(session, user, product, [review])
        assert ok is False
        assert len(sent) == 1  # без изменений

        # 3) Мастер-выключатель
        user.notify_new_reviews = True
        user.notifications_enabled = False
        await session.commit()
        ok = await notify_svc.notify_new_reviews(session, user, product, [review])
        assert ok is False
        assert len(sent) == 1


def test_format_new_reviews_text():
    product = Product(marketplace="wildberries", article="1", name="Плед")
    reviews = [
        Review(source="wb", text="отличный", rating=5),
        Review(source="wb", text="норм", rating=4),
    ]
    text = notify_svc._format_new_reviews(product, reviews)
    assert "Плед" in text
    assert "2" in text
