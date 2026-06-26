"""Решение капчи. Абстракция + адаптер 2captcha/rucaptcha (совместимый API).

Если провайдер `none` или нет ключа — возвращается NoCaptchaSolver, который
бросает CaptchaRequired. Так бизнес-логика получает понятную ошибку, а не
зависает. Сменить вендора = поменять адаптер, интерфейс остаётся прежним.
"""

from __future__ import annotations

import abc
import asyncio
import logging

import httpx

from app.config import settings
from app.providers.base import CaptchaRequired

logger = logging.getLogger(__name__)


class CaptchaSolver(abc.ABC):
    @abc.abstractmethod
    async def solve_recaptcha(self, site_key: str, page_url: str) -> str:
        """Возвращает токен g-recaptcha-response."""

    @abc.abstractmethod
    async def solve_image(self, image_b64: str) -> str:
        """Возвращает распознанный текст с картинки."""


class NoCaptchaSolver(CaptchaSolver):
    async def solve_recaptcha(self, site_key: str, page_url: str) -> str:
        raise CaptchaRequired(
            "Источник запросил капчу, но решатель не настроен "
            "(CAPTCHA_API_KEY пуст)."
        )

    async def solve_image(self, image_b64: str) -> str:
        raise CaptchaRequired(
            "Источник запросил капчу, но решатель не настроен "
            "(CAPTCHA_API_KEY пуст)."
        )


class TwoCaptchaSolver(CaptchaSolver):
    """2captcha/rucaptcha. base_url переключает между сервисами."""

    def __init__(self, api_key: str, base_url: str, poll_interval: float = 5.0,
                 timeout_s: float = 180.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.poll_interval = poll_interval
        self.timeout_s = timeout_s

    async def _submit(self, client: httpx.AsyncClient, data: dict) -> str:
        data = {**data, "key": self.api_key, "json": 1}
        resp = await client.post(f"{self.base_url}/in.php", data=data)
        payload = resp.json()
        if payload.get("status") != 1:
            raise CaptchaRequired(f"Капча: ошибка отправки: {payload.get('request')}")
        return payload["request"]

    async def _poll(self, client: httpx.AsyncClient, captcha_id: str) -> str:
        deadline = asyncio.get_event_loop().time() + self.timeout_s
        while asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(self.poll_interval)
            resp = await client.get(
                f"{self.base_url}/res.php",
                params={
                    "key": self.api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1,
                },
            )
            payload = resp.json()
            if payload.get("status") == 1:
                return payload["request"]
            if payload.get("request") != "CAPCHA_NOT_READY":
                raise CaptchaRequired(f"Капча: ошибка решения: {payload.get('request')}")
        raise CaptchaRequired("Капча: превышено время ожидания решения")

    async def solve_recaptcha(self, site_key: str, page_url: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            cid = await self._submit(
                client,
                {
                    "method": "userrecaptcha",
                    "googlekey": site_key,
                    "pageurl": page_url,
                },
            )
            return await self._poll(client, cid)

    async def solve_image(self, image_b64: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            cid = await self._submit(
                client, {"method": "base64", "body": image_b64}
            )
            return await self._poll(client, cid)


def get_captcha_solver() -> CaptchaSolver:
    if settings.captcha_provider == "twocaptcha" and settings.captcha_api_key:
        return TwoCaptchaSolver(
            settings.captcha_api_key, settings.captcha_base_url
        )
    return NoCaptchaSolver()
