"""Этап 8: репрайсер, безубыточность, промо-калькулятор."""

from app.services.pricing import (
    RepriceRule,
    break_even_price,
    compute_promo,
    compute_reprice,
)
from app.services.unit_economics import EconomicsParams


def test_reprice_undercut():
    r = compute_reprice(
        1000, [1100, 1050, 1200], RepriceRule(enabled=True, undercut_pct=5)
    )
    assert r.lowest_competitor == 1050
    assert r.target_price == 998  # 1050 * 0.95 = 997.5 -> 998
    assert r.recommended_price == 998
    assert r.direction == "down"
    assert r.would_change is True


def test_reprice_respects_min_price():
    r = compute_reprice(
        1000,
        [900],
        RepriceRule(enabled=True, undercut_pct=10, min_price=880),
    )
    # target = 810, но floor 880 -> не демпингуем
    assert r.recommended_price == 880
    assert r.floor_hit is True


def test_reprice_no_competitors():
    r = compute_reprice(1000, [], RepriceRule(enabled=True, undercut_pct=5))
    assert r.recommended_price == 1000
    assert r.would_change is False
    assert r.lowest_competitor is None


def test_reprice_max_price_cap():
    r = compute_reprice(
        500, [2000], RepriceRule(enabled=True, undercut_pct=0, max_price=1500)
    )
    assert r.recommended_price == 1500
    assert r.direction == "up"


def test_break_even():
    params = EconomicsParams(commission_pct=15, tax_pct=6, acquiring_pct=1.5)
    be = break_even_price(300, params)
    # fixed=300, k=0.225, be=300/0.775=387.10
    assert be == 387.1


def test_break_even_impossible():
    assert break_even_price(100, EconomicsParams(commission_pct=120)) is None


def test_promo_by_discount():
    params = EconomicsParams(commission_pct=15)
    r = compute_promo(1000, 300, params, discount_pct=20)
    assert r.promo_price == 800.0
    assert r.discount_pct == 20
    # промо economics: 800 - 300 - 120 = 380
    assert r.net_profit == 380.0
    # базовая: 1000 - 300 - 150 = 550 -> delta -170
    assert r.profit_delta == -170.0
    assert r.is_profitable is True


def test_promo_by_price_unprofitable():
    params = EconomicsParams(commission_pct=15)
    r = compute_promo(1000, 800, params, promo_price=850)
    # 850 - 800 - 127.5 = -77.5
    assert r.net_profit == -77.5
    assert r.is_profitable is False


def _create_product(client) -> int:
    return client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]


def test_repricer_api_with_competitor(client):
    pid = _create_product(client)  # price 3499
    client.post(
        f"/products/{pid}/competitors",
        json={"marketplace": "wildberries", "article": "555",
              "name": "Конкурент", "price": 3200},
    )
    save = client.put(
        f"/products/{pid}/repricer",
        json={"enabled": True, "undercut_pct": 5, "min_price": 2500},
    )
    assert save.status_code == 200, save.text
    body = save.json()
    assert body["lowest_competitor"] == 3200
    assert body["recommended_price"] == 3040  # 3200*0.95
    assert body["direction"] == "down"

    # сохранилось
    assert client.get(f"/products/{pid}/repricer").json()["rule"]["undercut_pct"] == 5


def test_promo_api(client):
    pid = _create_product(client)
    client.put(
        f"/products/{pid}/unit-economics", json={"commission_pct": 15}
    )
    r = client.post(f"/products/{pid}/promo-calc", json={"discount_pct": 10})
    assert r.status_code == 200, r.text
    assert r.json()["promo_price"] == 3149.1
