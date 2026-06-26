"""Фабрика LLM-провайдера."""

from __future__ import annotations

from app.ai.base import LLMProvider, NoLLMProvider
from app.config import settings


def get_llm() -> LLMProvider:
    if settings.llm_provider == "claude" and settings.anthropic_api_key:
        from app.ai.claude import build_claude_provider

        return build_claude_provider()
    return NoLLMProvider()
