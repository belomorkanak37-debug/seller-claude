from app.scraping.parsers import parse_ldjson_itemlist


def test_parse_itemlist_with_listitems():
    html = """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "item": {
            "@type": "Product", "name": "Плед А", "url": "https://m/product/111",
            "image": "https://img/a.jpg",
            "offers": {"price": "1200"},
            "aggregateRating": {"ratingValue": "4.6", "reviewCount": "12"}
        }},
        {"@type": "ListItem", "position": 2, "item": {
            "@type": "Product", "name": "Плед Б", "url": "https://m/product/222",
            "offers": {"price": "1500"}
        }}
      ]
    }
    </script>
    """
    items = parse_ldjson_itemlist(html)
    assert len(items) == 2
    assert items[0]["name"] == "Плед А"
    assert items[0]["price"] == 1200.0
    assert items[0]["rating"] == 4.6
    assert items[0]["reviews_count"] == 12
    assert items[1]["name"] == "Плед Б"


def test_parse_itemlist_empty():
    assert parse_ldjson_itemlist("<html></html>") == []
