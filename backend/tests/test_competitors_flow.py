"""Поток Этапа 3: поиск конкурентов -> добавление -> отзывы -> заметка -> удаление."""


def _create_product(client) -> int:
    return client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]


def test_search_returns_keywords_and_excludes_own(client):
    pid = _create_product(client)
    r = client.get(f"/products/{pid}/competitors/search")
    assert r.status_code == 200, r.text
    data = r.json()
    # ключевые слова выделены из названия "Комод белый 4 ящика"
    assert "комод" in data["keywords"]
    # собственный товар (article=123) исключён, конкурент 555 остался
    arts = [c["article"] for c in data["competitors"]]
    assert "123" not in arts
    assert "555" in arts


def test_add_competitor_enriches_reviews_and_tags(client):
    pid = _create_product(client)
    r = client.post(
        f"/products/{pid}/competitors",
        json={
            "marketplace": "wildberries",
            "article": "555",
            "name": "Комод дубовый конкурент",
            "price": 4100,
            "rating": 4.5,
            "url": "https://www.wildberries.ru/catalog/555/detail.aspx",
        },
    )
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    # теги подтянулись из get_product фейка
    assert r.json()["tags"] == ["Цвет: белый", "Материал: ЛДСП"]

    # отзывы конкурента сохранены
    rev = client.get(f"/competitors/{cid}/reviews")
    assert rev.status_code == 200
    assert len(rev.json()) == 1
    assert rev.json()[0]["author"] == "Анна"


def test_list_competitors(client):
    pid = _create_product(client)
    client.post(
        f"/products/{pid}/competitors",
        json={"marketplace": "wildberries", "article": "555", "name": "Конкурент"},
    )
    r = client.get(f"/products/{pid}/competitors")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_update_note(client):
    pid = _create_product(client)
    cid = client.post(
        f"/products/{pid}/competitors",
        json={"marketplace": "wildberries", "article": "555", "name": "Конкурент"},
    ).json()["id"]
    r = client.patch(
        f"/competitors/{cid}", json={"note": "демпингует по выходным"}
    )
    assert r.status_code == 200
    assert r.json()["note"] == "демпингует по выходным"


def test_delete_competitor(client):
    pid = _create_product(client)
    cid = client.post(
        f"/products/{pid}/competitors",
        json={"marketplace": "wildberries", "article": "555", "name": "Конкурент"},
    ).json()["id"]
    assert client.delete(f"/competitors/{cid}").status_code == 204
    assert client.get(f"/products/{pid}/competitors").json() == []
