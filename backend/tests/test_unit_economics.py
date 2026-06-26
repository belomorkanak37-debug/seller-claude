"""Этап 6: юнит-экономика — расчёт и сохранение."""

from app.services.unit_economics import EconomicsParams, compute_economics


def test_compute_profitable():
    # цена 1000, себестоимость 300, комиссия 15%, эквайринг 1.5%, налог 6%,
    # возвраты 2%, логистика 50, хранение 10
    params = EconomicsParams(
        commission_pct=15,
        acquiring_pct=1.5,
        tax_pct=6,
        returns_pct=2,
        logistics_cost=50,
        storage_cost=10,
    )
    r = compute_economics(1000, 300, params)
    # затраты: 300 + 150 + 15 + 60 + 20 + 50 + 10 = 605
    assert r.total_costs == 605.0
    assert r.net_profit == 395.0
    assert r.margin_pct == 39.5
    assert r.is_profitable is True


def test_compute_loss():
    params = EconomicsParams(commission_pct=30, logistics_cost=200)
    r = compute_economics(500, 400, params)
    # затраты: 400 + 150 + 200 = 750 -> прибыль -250
    assert r.net_profit == -250.0
    assert r.is_profitable is False


def test_compute_zero_price():
    r = compute_economics(0, 0, EconomicsParams())
    assert r.margin_pct is None
    assert r.net_profit == 0.0


def _create_product(client) -> int:
    return client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]


def test_get_defaults_then_save(client):
    pid = _create_product(client)  # price 3499, cost None

    r = client.get(f"/products/{pid}/unit-economics")
    assert r.status_code == 200, r.text
    # без параметров: затраты только себестоимость(0) -> прибыль = цена
    assert r.json()["net_profit"] == 3499.0
    assert r.json()["params"]["commission_pct"] == 0

    save = client.put(
        f"/products/{pid}/unit-economics",
        json={"commission_pct": 15, "tax_pct": 6, "logistics_cost": 100},
    )
    assert save.status_code == 200, save.text
    body = save.json()
    # 3499 - (524.85 + 209.94 + 100) = 2664.21
    assert body["breakdown"]["commission"] == 524.85
    assert body["net_profit"] == 2664.21
    assert body["is_profitable"] is True

    # параметры сохранились
    again = client.get(f"/products/{pid}/unit-economics")
    assert again.json()["params"]["commission_pct"] == 15
    assert again.json()["net_profit"] == 2664.21
