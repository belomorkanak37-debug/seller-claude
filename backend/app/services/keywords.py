"""Выделение ключевых слов из названия товара для поиска конкурентов.

Идея ТЗ: искать по 2–4 ключевым словам (категория + главное свойство:
«комод», «плед», «игрушка», «наполнитель»…), а не по полному названию.

Без тяжёлых NLP-зависимостей: нижний регистр, выкидываем стоп-слова, числа,
размеры/единицы измерения и слишком короткие токены; сохраняем порядок
(первое слово в названии обычно и есть категория).
"""

from __future__ import annotations

import re

# Частые стоп-слова и «шумовые» слова в названиях карточек.
_STOPWORDS: set[str] = {
    "для", "под", "над", "без", "при", "про", "это", "что", "как", "или",
    "и", "в", "во", "с", "со", "на", "из", "от", "до", "по", "за", "не",
    "the", "and", "for", "with", "set", "pcs", "шт", "штук", "штука",
    "размер", "размером", "цвет", "цвета", "новый", "новинка", "хит",
    "распродажа", "акция", "оригинал", "оригинальный", "подарок", "premium",
    "люкс", "set", "kit",
}

# Единицы измерения / размерные суффиксы.
_UNITS: set[str] = {
    "см", "мм", "м", "кг", "г", "гр", "мл", "л", "вт", "ватт", "ah", "мач",
    "x", "х", "хх",
}

_TOKEN_RE = re.compile(r"[а-яёa-z0-9]+", re.IGNORECASE)
_HAS_DIGIT_RE = re.compile(r"\d")


def _is_meaningful(token: str) -> bool:
    if len(token) < 3:
        return False
    if token in _STOPWORDS or token in _UNITS:
        return False
    # Размеры/числа/артикулы: содержат цифру -> отбрасываем (150x200, 4шт, 2024)
    if _HAS_DIGIT_RE.search(token):
        return False
    return True


def extract_keywords(name: str, max_keywords: int = 4) -> list[str]:
    """Возвращает 2–4 (до max_keywords) ключевых слова в порядке появления."""
    if not name:
        return []
    tokens = _TOKEN_RE.findall(name.lower())
    result: list[str] = []
    seen: set[str] = set()
    for tok in tokens:
        if not _is_meaningful(tok):
            continue
        if tok in seen:
            continue
        seen.add(tok)
        result.append(tok)
        if len(result) >= max_keywords:
            break
    return result
