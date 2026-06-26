import json

from app.scraping.parsers import parse_ldjson_product, parse_ozon_composer


SAMPLE_LDJSON_HTML = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Плед флисовый 150x200",
  "image": ["https://img.example/1.jpg"],
  "brand": {"@type": "Brand", "name": "ТеплоДом"},
  "offers": {"@type": "Offer", "price": "1299", "priceCurrency": "RUB"},
  "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.8", "reviewCount": "256"}
}
</script>
</head><body></body></html>
"""


def test_parse_ldjson_product():
    data = parse_ldjson_product(SAMPLE_LDJSON_HTML)
    assert data["name"] == "Плед флисовый 150x200"
    assert data["photo_url"] == "https://img.example/1.jpg"
    assert data["price"] == 1299.0
    assert data["rating"] == 4.8
    assert data["reviews_count"] == 256
    assert data["brand"] == "ТеплоДом"


def test_parse_ldjson_absent_returns_empty():
    assert parse_ldjson_product("<html></html>") == {}


def test_parse_ldjson_graph_container():
    html = """
    <script type="application/ld+json">
    {"@graph": [
      {"@type": "BreadcrumbList"},
      {"@type": "Product", "name": "Комод", "offers": {"price": 4999}}
    ]}
    </script>
    """
    data = parse_ldjson_product(html)
    assert data["name"] == "Комод"
    assert data["price"] == 4999.0


def test_parse_ozon_composer():
    composer = {
        "widgetStates": {
            "webProductHeading-100": json.dumps({"title": "Игрушка мягкая Мишка"}),
            "webPrice-200": json.dumps({"cardPrice": "999 ₽", "price": "1 199 ₽"}),
            "webReviewProductScore-300": json.dumps(
                {"totalScore": "4.9", "reviewsCount": 1024}
            ),
            "webGallery-400": json.dumps(
                {"images": [{"src": "https://ozon.img/1.jpg"}]}
            ),
            "webCharacteristics-500": json.dumps(
                {
                    "characteristics": [
                        {"short": [{"name": "Цвет", "text": "коричневый"}]}
                    ]
                }
            ),
        }
    }
    data = parse_ozon_composer(composer)
    assert data["name"] == "Игрушка мягкая Мишка"
    assert data["price"] == 999.0
    assert data["rating"] == 4.9
    assert data["reviews_count"] == 1024
    assert data["photo_url"] == "https://ozon.img/1.jpg"
    assert data["tags"] == ["Цвет: коричневый"]


def test_parse_ozon_composer_empty():
    assert parse_ozon_composer({"widgetStates": {}}) == {}
