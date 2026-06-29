"""Этап 11: реклама (ДРР/ROI) и финансы (выплаты, P&L)."""

from app.services.advertising import compute_ad_metrics


def test_ad_metrics_drr_roi():
    m = compute_ad_metrics(spend=1000, revenue=5000, clicks=500, orders=50)
    assert m.drr == 20.0          # 1000/5000
    assert m.roi == 400.0         # (5000-1000)/1000
    assert m.cpo == 20.0          # 1000/50
    assert m.cpc == 2.0           # 1000/500
    assert "ДРР" in m.recommendation


def test_ad_metrics_high_drr_recommendation():
    m = compute_ad_metrics(spend=600, revenue=2000)
    assert m.drr == 30.0
    assert "снизьте" in m.recommendation.lower() or "снизить" in m.recommendation.lower()


def test_ad_metrics_zero_revenue():
    m = compute_ad_metrics(spend=500, revenue=0)
    assert m.drr is None
    assert m.roi == -100.0


def _create_product(client) -> int:
    return client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]


def test_ads_crud_and_aggregate(client):
    pid = _create_product(client)
    client.post(
        f"/products/{pid}/ads",
        json={"label": "Май", "spend": 1000, "revenue": 4000, "clicks": 200, "orders": 40},
    )
    client.post(
        f"/products/{pid}/ads",
        json={"label": "Июнь", "spend": 1000, "revenue": 6000, "clicks": 300, "orders": 60},
    )
    r = client.get(f"/products/{pid}/ads")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["stats"]) == 2
    # агрегат: spend 2000, revenue 10000 -> ДРР 20%
    assert body["total"]["drr"] == 20.0
    assert body["total"]["orders"] == 100


def test_payouts_summary(client):
    client.post("/payouts", json={"type": "payout", "amount": 10000})
    client.post("/payouts", json={"type": "fine", "amount": 500})
    client.post("/payouts", json={"type": "withholding", "amount": 300})
    client.post("/payouts", json={"type": "correction", "amount": 200})

    r = client.get("/payouts")
    assert r.status_code == 200
    s = r.json()["summary"]
    assert s["payout"] == 10000
    assert s["fine"] == 500
    # net = 10000 + 200 - 500 - 300 = 9400
    assert s["net"] == 9400.0


def test_payout_invalid_type(client):
    r = client.post("/payouts", json={"type": "bogus", "amount": 1})
    assert r.status_code == 400


def test_pnl(client):
    pid = _create_product(client)  # price 3499
    # параметры экономики: комиссия 15%
    client.put(f"/products/{pid}/unit-economics", json={"commission_pct": 15})
    # реклама: 5000 расходов
    client.post(
        f"/products/{pid}/ads",
        json={"label": "Май", "spend": 5000, "revenue": 20000},
    )
    # штраф 1000 по этому товару
    client.post(
        "/payouts", json={"type": "fine", "amount": 1000, "product_id": pid}
    )

    r = client.get(f"/products/{pid}/pnl", params={"units": 10})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["units"] == 10
    assert b["revenue"] == 34990.0                 # 3499*10
    assert b["ad_costs"] == 5000.0
    assert b["adjustments"] == -1000.0             # штраф
    # marketplace_costs = комиссия 15% от 3499 *10 = 5248.5
    assert b["marketplace_costs"] == 5248.5
    # net = 34990 - (0 + 5248.5 + 5000) - 1000 = 23741.5
    assert b["net_profit"] == 23741.5
