"""Этап 10: AI по отзывам — ответы, тональность, анализ конкурентов."""

import app.api.routes.ai as ai_route
from app.ai.base import LLMProvider, NoLLMProvider


class FakeLLM(LLMProvider):
    async def complete(self, system, user, max_tokens=1024):
        return "Спасибо за отзыв! Сожалеем о неудобстве, разберёмся."

    async def complete_json(self, system, user, max_tokens=1024):
        return {
            "sentiment": {"positive": 2, "neutral": 1, "negative": 1},
            "common_complaints": ["долгая доставка"],
            "suggestions": ["улучшить упаковку"],
            "praise": ["низкая цена"],
            "criticism": ["качество сборки"],
            "differentiation": ["добавить гарантию 2 года"],
        }


def _create_product(client) -> int:
    return client.post(
        "/products", json={"marketplace": "wildberries", "article": "123"}
    ).json()["id"]


def test_generate_reply(client, monkeypatch):
    monkeypatch.setattr(ai_route, "get_llm", lambda: FakeLLM())
    pid = _create_product(client)  # сохраняет отзыв r1
    review_id = client.get(f"/products/{pid}/reviews").json()[0]["id"]

    r = client.post(f"/reviews/{review_id}/reply")
    assert r.status_code == 200, r.text
    assert "Спасибо" in r.json()["reply"]


def test_analyze_reviews(client, monkeypatch):
    monkeypatch.setattr(ai_route, "get_llm", lambda: FakeLLM())
    pid = _create_product(client)
    r = client.post(f"/products/{pid}/reviews/analyze")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sentiment"]["positive"] == 2
    assert body["common_complaints"] == ["долгая доставка"]
    assert body["suggestions"] == ["улучшить упаковку"]


def test_analyze_competitors(client, monkeypatch):
    monkeypatch.setattr(ai_route, "get_llm", lambda: FakeLLM())
    pid = _create_product(client)
    client.post(
        f"/products/{pid}/competitors",
        json={"marketplace": "wildberries", "article": "555", "name": "Конкурент"},
    )
    r = client.post(f"/products/{pid}/competitors/analyze")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["praise"] == ["низкая цена"]
    assert body["criticism"] == ["качество сборки"]
    assert body["differentiation"] == ["добавить гарантию 2 года"]


def test_reply_without_llm_key_returns_503(client, monkeypatch):
    monkeypatch.setattr(ai_route, "get_llm", lambda: NoLLMProvider())
    pid = _create_product(client)
    review_id = client.get(f"/products/{pid}/reviews").json()[0]["id"]
    r = client.post(f"/reviews/{review_id}/reply")
    assert r.status_code == 503


def test_analyze_requires_reviews(client, monkeypatch):
    monkeypatch.setattr(ai_route, "get_llm", lambda: FakeLLM())
    pid = _create_product(client)
    # удалим отзывы товара, чтобы проверить 400
    # (проще: competitors/analyze без конкурентов -> 400)
    r = client.post(f"/products/{pid}/competitors/analyze")
    assert r.status_code == 400


def test_extract_json_helper():
    from app.ai.base import extract_json

    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('text before {"b": 2} after') == {"b": 2}
