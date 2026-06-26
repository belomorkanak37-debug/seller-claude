"""Юнит-тесты парсинга ответов Wildberries (без сети, синтетические данные)."""

from app.providers.wildberries import (
    WildberriesProvider,
    _extract_price,
    _extract_rating,
    _extract_stock,
    wb_image_url,
)


def _sample_product():
    return {
        "id": 123456789,
        "root": 111,
        "name": "Комод белый 4 ящика",
        "brand": "ИКЕА",
        "reviewRating": 4.7,
        "feedbacks": 320,
        "sizes": [
            {
                "price": {"basic": 500000, "product": 349900, "total": 349900},
                "stocks": [{"qty": 12}, {"qty": 3}],
            }
        ],
    }


def test_extract_price_from_sizes_kopecks():
    assert _extract_price(_sample_product()) == 3499.0


def test_extract_price_fallback_old_fields():
    assert _extract_price({"salePriceU": 199900, "sizes": []}) == 1999.0


def test_extract_stock_sums_qty():
    assert _extract_stock(_sample_product()) == 15


def test_extract_stock_none_when_absent():
    assert _extract_stock({"sizes": [{"stocks": []}]}) is None


def test_extract_rating_prefers_review_rating():
    assert _extract_rating(_sample_product()) == 4.7


def test_image_url_shape():
    url = wb_image_url(123456789)
    assert url.startswith("https://basket-")
    assert "/vol1234/part123456/123456789/images/big/1.webp" in url


def test_parse_feedbacks_combines_pros_cons():
    fbs = [
        {
            "id": "a1",
            "text": "отличный комод",
            "pros": "крепкий",
            "cons": "долго собирать",
            "productValuation": 5,
            "createdDate": "2026-01-02T10:00:00Z",
            "wbUserDetails": {"name": "Анна"},
        }
    ]
    reviews = WildberriesProvider._parse_feedbacks(fbs, 30)
    assert len(reviews) == 1
    r = reviews[0]
    assert r.rating == 5
    assert r.author == "Анна"
    assert "крепкий" in r.text and "долго собирать" in r.text
    assert r.published_at is not None
