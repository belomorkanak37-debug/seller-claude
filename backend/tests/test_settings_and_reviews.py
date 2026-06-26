"""Этап 4: настройки уведомлений и обновление отзывов."""

from tests.conftest import FakeWildberriesProvider, _review


def _create_product(client) -> int:
    return client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]


def test_me_returns_settings(client):
    r = client.get("/me")
    assert r.status_code == 200
    assert r.json()["notifications_enabled"] is True
    assert r.json()["notify_new_reviews"] is True


def test_update_settings(client):
    r = client.patch("/me/settings", json={"notify_new_reviews": False})
    assert r.status_code == 200
    assert r.json()["notify_new_reviews"] is False
    assert r.json()["notifications_enabled"] is True
    # перечитываем
    assert client.get("/me").json()["notify_new_reviews"] is False


def test_refresh_reviews_dedup_no_new(client):
    pid = _create_product(client)  # уже сохранил r1 при создании
    r = client.post(f"/products/{pid}/reviews/refresh")
    assert r.status_code == 200, r.text
    assert r.json()["new"] == 0
    assert r.json()["total"] == 1


def test_refresh_reviews_detects_new(client):
    pid = _create_product(client)
    # источник «получил» новый отзыв
    FakeWildberriesProvider.EXTRA_REVIEWS = [_review("r2", "Борис", "супер", 5)]
    r = client.post(f"/products/{pid}/reviews/refresh")
    assert r.status_code == 200, r.text
    assert r.json()["new"] == 1
    assert r.json()["total"] == 2


def test_notifications_log_empty_initially(client):
    assert client.get("/notifications").json() == []
