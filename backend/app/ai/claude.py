"""Адаптер Claude (официальный SDK anthropic).

По умолчанию модель claude-opus-4-8. Ленивая инициализация клиента, чтобы
импорт модуля не требовал установленного SDK (важно для тестов с фейком).
"""

from __future__ import annotations

import logging

from app.ai.base import LLMError, LLMProvider
from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        client = self._get_client()
        try:
            message = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Claude completion error: %s", exc)
            raise LLMError(f"Ошибка обращения к модели: {exc}") from exc

        return "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        ).strip()


def build_claude_provider() -> ClaudeProvider:
    return ClaudeProvider(settings.anthropic_api_key, settings.llm_model)
