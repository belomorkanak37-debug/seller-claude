import pytest

from app.providers.base import CaptchaRequired
from app.scraping import captcha as cap


@pytest.mark.asyncio
async def test_no_captcha_solver_raises():
    solver = cap.NoCaptchaSolver()
    with pytest.raises(CaptchaRequired):
        await solver.solve_recaptcha("sitekey", "https://x")
    with pytest.raises(CaptchaRequired):
        await solver.solve_image("base64data")


def test_get_solver_none_without_key(monkeypatch):
    monkeypatch.setattr(cap.settings, "captcha_provider", "twocaptcha")
    monkeypatch.setattr(cap.settings, "captcha_api_key", "")
    assert isinstance(cap.get_captcha_solver(), cap.NoCaptchaSolver)


def test_get_solver_twocaptcha_with_key(monkeypatch):
    monkeypatch.setattr(cap.settings, "captcha_provider", "twocaptcha")
    monkeypatch.setattr(cap.settings, "captcha_api_key", "KEY123")
    solver = cap.get_captcha_solver()
    assert isinstance(solver, cap.TwoCaptchaSolver)
    assert solver.api_key == "KEY123"
