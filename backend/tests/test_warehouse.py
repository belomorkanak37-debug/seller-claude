"""Этап 7: склад — прогноз остатка, рекомендация по отгрузке, статусы."""

import pytest
from sqlalchemy import select

from app.db.models import Competitor, Product, User
from app.services import notifications as notify_svc
from app.services.warehouse import WarehouseParams, compute_forecast


def test_forecast_ok():
    f = compute_forecast(
        300, WarehouseParams(daily_sales=5, lead_time_days=14, target_cover_days=30,
                             low_stock_threshold_days=7)
    )
    assert f.days_left == 60  # 300 / 5
    assert f.status == "ok"
    # target = 5*(14+30)=220, остаток 300 -> отгрузка не нужна
    assert f.recommended_supply == 0


def test_forecast_low_and_reorder():
    f = compute_forecast(
        20, WarehouseParams(daily_sales=5, lead_time_days=14, target_cover_days=30,
                            low_stock_threshold_days=7)
    )
    assert f.days_left == 4  # 20/5
    assert f.status == "critical"  # 4 <= lead_time(14)
    # target=220, остаток 20 -> отгрузить 200
    assert f.recommended_supply == 200


def test_forecast_low_status():
    f = compute_forecast(
        30, WarehouseParams(daily_sales=5, lead_time_days=3, target_cover_days=30,
                            low_stock_threshold_days=7)
    )
    assert f.days_left == 6
    assert f.status == "low"  # 6 > lead_time(3) но <= threshold(7)


def test_forecast_out():
    f = compute_forecast(0, WarehouseParams(daily_sales=5))
    assert f.status == "out"
    assert f.days_left == 0


def test_forecast_unknown_without_sales():
    f = compute_forecast(50, WarehouseParams(daily_sales=0))
    assert f.status == "unknown"
    assert f.days_left is None
    assert f.recommended_supply == 0


def _create_product(client) -> int:
    return client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]


def test_warehouse_api_get_and_save(client):
    pid = _create_product(client)  # stock=15 из фейка
    r = client.get(f"/products/{pid}/warehouse")
    assert r.status_code == 200, r.text
    assert r.json()["stock"] == 15
    assert r.json()["status"] == "unknown"  # daily_sales=0

    save = client.put(
        f"/products/{pid}/warehouse",
        json={"daily_sales": 3, "lead_time_days": 10, "target_cover_days": 20,
              "low_stock_threshold_days": 7},
    )
    assert save.status_code == 200, save.text
    body = save.json()
    assert body["days_left"] == 5  # 15/3
    assert body["status"] == "critical"  # 5 <= 10
    # target=3*(10+20)=90, остаток 15 -> 75
    assert body["recommended_supply"] == 75

    # сохранилось
    assert client.get(f"/products/{pid}/warehouse").json()["params"]["daily_sales"] == 3


@pytest.mark.asyncio
async def test_notify_competitor_oos_gating(db, monkeypatch):
    sent = []

    async def fake_send(chat_id, text):
        sent.append(text)
        return True

    monkeypatch.setattr(notify_svc, "send_telegram_message", fake_send)

    async with db() as session:
        user = (await session.execute(select(User))).scalars().first()
        product = Product(user_id=user.id, marketplace="wildberries",
                          article="123", name="Комод")
        session.add(product)
        await session.flush()
        comp = Competitor(product_id=product.id, marketplace="wildberries",
                          article="555", name="Конкурент")
        session.add(comp)
        await session.commit()

        ok = await notify_svc.notify_competitor_oos(session, user, product, comp)
        assert ok is True and len(sent) == 1

        # выключаем складские уведомления
        user.notify_stock = False
        await session.commit()
        ok = await notify_svc.notify_competitor_oos(session, user, product, comp)
        assert ok is False and len(sent) == 1
