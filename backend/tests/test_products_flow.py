"""Интеграционные тесты потока Этапа 1: lookup → create → list → edit → delete."""


def test_lookup_returns_live_card_and_reviews(client):
    r = client.get(
        "/products/lookup",
        params={"marketplace": "wildberries", "article": "123"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["name"] == "Комод белый 4 ящика"
    assert data["price"] == 3499.0
    assert data["rating"] == 4.7
    assert len(data["reviews"]) == 1
    assert data["tags"]


def test_create_persists_product_and_reviews(client):
    r = client.post(
        "/products",
        json={"marketplace": "wildberries", "article": "123", "cost_price": 1500},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    assert float(r.json()["price"]) == 3499.0
    assert r.json()["tags"] == ["Цвет: белый", "Материал: ЛДСП"]

    # отзывы сохранены
    rev = client.get(f"/products/{pid}/reviews")
    assert rev.status_code == 200
    assert len(rev.json()) == 1
    assert rev.json()[0]["author"] == "Анна"


def test_list_contains_created_product(client):
    client.post("/products", json={"marketplace": "wildberries", "article": "123"})
    r = client.get("/products")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_edit_any_field(client):
    pid = client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]

    r = client.patch(
        f"/products/{pid}",
        json={"name": "Комод дубовый", "price": 4200, "notes": "хит продаж"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Комод дубовый"
    assert float(r.json()["price"]) == 4200.0
    assert r.json()["notes"] == "хит продаж"


def test_delete_product(client):
    pid = client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]
    assert client.delete(f"/products/{pid}").status_code == 204
    assert client.get("/products").json() == []


def test_get_missing_product_404(client):
    assert client.get("/products/99999").status_code == 404
