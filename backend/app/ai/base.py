"""Абстракция LLM-провайдера.

За интерфейсом скрыт конкретный провайдер (по умолчанию Claude). Без ключа
возвращается NoLLMProvider, который даёт понятную ошибку, а не падает молча —
тот же приём, что и для капчи на Этапе 2.
"""

from __future__ import annotations

import abc
import json
import re


class LLMError(Exception):
    """Базовая ошибка LLM-слоя."""


class LLMNotConfigured(LLMError):
    """LLM-провайдер не настроен (нет ключа)."""


def extract_json(text: str) -> dict | list:
    """Достаёт JSON из ответа модели (в т.ч. из ```json ... ``` блоков)."""
    text = text.strip()
    # срезаем markdown-ограждение, если есть
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    # пытаемся найти первый JSON-объект/массив и декодировать, игнорируя хвост
    start = min(
        [i for i in (text.find("{"), text.find("[")) if i != -1] or [0]
    )
    decoder = json.JSONDecoder()
    try:
        obj, _ = decoder.raw_decode(text[start:])
        return obj
    except json.JSONDecodeError:
        # последний шанс — весь текст целиком
        return json.loads(text)


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        """Возвращает текстовый ответ модели."""

    async def complete_json(
        self, system: str, user: str, max_tokens: int = 1024
    ) -> dict | list:
        """Просит модель вернуть JSON и парсит его."""
        instruction = (
            f"{system}\n\nОтвечай СТРОГО валидным JSON без пояснений и markdown."
        )
        raw = await self.complete(instruction, user, max_tokens=max_tokens)
        return extract_json(raw)


class NoLLMProvider(LLMProvider):
    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        raise LLMNotConfigured(
            "LLM не настроен: задайте ANTHROPIC_API_KEY (или LLM_PROVIDER=claude)."
        )
