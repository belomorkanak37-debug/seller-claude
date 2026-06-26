"""Этап 5: снапшоты цен и история (только реальные накопленные данные)."""

from tests.conftest import FakeWildberriesProvider


def _create_product(client) -> int:
    return client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]


def test_history_empty_initially(client):
    pid = _create_product(client)
    r = client.get(f"/products/{pid}/price-history")
    assert r.status_code == 200, r.text
    assert r.json()["product"]["points"] == []
    assert r.json()["competitors"] == []


def test_snapshot_then_history_has_points(client):
    pid = _create_product(client)
    # добавим конкурента, чтобы снимок взял и его
    client.post(
        f"/products/{pid}/competitors",
        json={"marketplace": "wildberries", "article": "555", "name": "Конкурент"},
    )

    snap = client.post(f"/products/{pid}/price-snapshot")
    assert snap.status_code == 200, snap.text
    assert snap.json() == {"product": 1, "competitors": 1}

    r = client.get(f"/products/{pid}/price-history")
    data = r.json()
    assert len(data["product"]["points"]) == 1
    assert data["product"]["points"][0]["price"] == 3499.0
    assert len(data["competitors"]) == 1
    assert len(data["competitors"][0]["points"]) == 1


def test_history_accumulates_across_snapshots(client):
    pid = _create_product(client)
    client.post(f"/products/{pid}/price-snapshot")
    # цена изменилась — следующий снимок отразит это
    FakeWildberriesProvider.PRICE = 3299.0
    client.post(f"/products/{pid}/price-snapshot")

    points = client.get(f"/products/{pid}/price-history").json()["product"]["points"]
    assert len(points) == 2
    assert [p["price"] for p in points] == [3499.0, 3299.0]
