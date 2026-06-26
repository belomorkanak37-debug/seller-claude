"""Этап 9: позиции, сравнение карточки, SEO."""

from app.services.cards import score_card, suggest_keywords, CardMetrics
from app.services.positions import find_position


def test_find_position():
    assert find_position(["555", "123", "777"], "123") == 2
    assert find_position(["555", "777"], "123") is None


def test_suggest_keywords_excludes_own():
    s = suggest_keywords(
        "Комод белый 4 ящика",
        ["Комод дубовый конкурент", "Комод венге шкаф"],
    )
    assert "комод" not in s  # уже в нашем названии
    assert "дубовый" in s


def test_score_card_levels():
    full = CardMetrics(
        has_photo=True, rating=4.8, reviews_count=200, tags_count=15,
        price=1000, name_length=60,
    )
    score, tips = score_card(full)
    assert score == 100 and tips == []

    poor = CardMetrics(
        has_photo=False, rating=3.5, reviews_count=1, tags_count=0,
        price=None, name_length=5,
    )
    score2, tips2 = score_card(poor)
    assert score2 == 0 and len(tips2) == 5


def _create_product(client) -> int:
    return client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]


def test_positions_check_and_history(client):
    pid = _create_product(client)
    # фейк-поиск возвращает [555, 123] -> наш товар на позиции 2
    r = client.post(f"/products/{pid}/positions/check")
    assert r.status_code == 200, r.text
    assert r.json() == [{"query": "комод белый ящика", "position": 2}]

    hist = client.get(f"/products/{pid}/positions")
    assert hist.json()["queries"] == ["комод белый ящика"]
    assert hist.json()["history"][0]["points"][0]["position"] == 2


def test_tracked_queries_override(client):
    pid = _create_product(client)
    r = client.put(
        f"/products/{pid}/tracked-queries", json={"queries": ["комод недорого"]}
    )
    assert r.status_code == 200
    assert r.json()["queries"] == ["комод недорого"]


def test_card_comparison(client):
    pid = _create_product(client)
    client.post(
        f"/products/{pid}/competitors",
        json={"marketplace": "wildberries", "article": "555",
              "name": "Комод дубовый конкурент", "price": 4100,
              "rating": 4.9, "reviews_count": 500},
    )
    r = client.get(f"/products/{pid}/card-comparison")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "product" in body and "competitors_avg" in body
    assert isinstance(body["recommendations"], list) and body["recommendations"]


def test_seo(client):
    pid = _create_product(client)
    client.post(
        f"/products/{pid}/competitors",
        json={"marketplace": "wildberries", "article": "555",
              "name": "Комод дубовый конкурент", "price": 4100},
    )
    r = client.get(f"/products/{pid}/seo")
    assert r.status_code == 200, r.text
    assert 0 <= r.json()["score"] <= 100
    assert isinstance(r.json()["suggested_keywords"], list)
