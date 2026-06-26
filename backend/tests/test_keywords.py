from app.services.keywords import extract_keywords


def test_extracts_category_first():
    kw = extract_keywords("Комод белый 4 ящика ЛДСП 80x40")
    assert kw[0] == "комод"
    assert "белый" in kw
    # числа и размеры отброшены
    assert "80x40" not in kw and "4" not in kw


def test_drops_stopwords_and_units():
    kw = extract_keywords("Плед для дивана 150 см флисовый")
    assert "плед" in kw
    assert "для" not in kw
    assert "см" not in kw
    assert "150" not in kw


def test_limit_max_keywords():
    kw = extract_keywords(
        "Игрушка мягкая медведь плюшевый большой коричневый подарочный",
        max_keywords=3,
    )
    assert len(kw) == 3
    assert kw[0] == "игрушка"


def test_dedup_and_order_preserved():
    kw = extract_keywords("Наполнитель наполнитель синтепон синтепон")
    assert kw == ["наполнитель", "синтепон"]


def test_empty_name():
    assert extract_keywords("") == []
    assert extract_keywords("4 80x40 150") == []
