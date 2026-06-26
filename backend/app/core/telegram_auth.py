"""Серверная валидация Telegram WebApp initData.

Алгоритм (официальный):
1. Разобрать initData как query-string в пары key=value.
2. Выделить поле `hash`, остальное отсортировать по ключу.
3. Собрать data_check_string = "\n".join(f"{k}={v}").
4. secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token).
5. calc_hash = HMAC_SHA256(key=secret_key, msg=data_check_string).hex()
6. Сравнить calc_hash с присланным hash (constant-time).

Документация: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class InitDataError(Exception):
    """Невалидные или просроченные initData."""


@dataclass
class TelegramUser:
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    photo_url: str | None = None


@dataclass
class ParsedInitData:
    user: TelegramUser
    auth_date: int
    raw: dict[str, str]


def _build_secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def validate_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 86400,
) -> ParsedInitData:
    """Проверяет подпись initData и возвращает разобранные данные.

    Бросает InitDataError при любой проблеме (нет hash, неверная подпись,
    просрочено, нет пользователя).
    """
    if not init_data:
        raise InitDataError("Пустой initData")
    if not bot_token:
        raise InitDataError("BOT_TOKEN не сконфигурирован на сервере")

    # parse_qsl сохраняет порядок, но мы всё равно сортируем вручную.
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("В initData отсутствует hash")

    data_check_string = "\n".join(
        f"{k}={pairs[k]}" for k in sorted(pairs.keys())
    )

    secret_key = _build_secret_key(bot_token)
    calc_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calc_hash, received_hash):
        raise InitDataError("Подпись initData не совпадает")

    # Проверка возраста (защита от replay)
    auth_date_raw = pairs.get("auth_date")
    if not auth_date_raw or not auth_date_raw.isdigit():
        raise InitDataError("Некорректный auth_date")
    auth_date = int(auth_date_raw)

    if max_age_seconds > 0 and (time.time() - auth_date) > max_age_seconds:
        raise InitDataError("initData просрочен")

    # Пользователь приходит JSON-строкой в поле user
    user_raw = pairs.get("user")
    if not user_raw:
        raise InitDataError("В initData отсутствует user")

    try:
        user_dict = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise InitDataError("Невозможно разобрать user") from exc

    if "id" not in user_dict:
        raise InitDataError("В user отсутствует id")

    user = TelegramUser(
        id=int(user_dict["id"]),
        first_name=user_dict.get("first_name"),
        last_name=user_dict.get("last_name"),
        username=user_dict.get("username"),
        language_code=user_dict.get("language_code"),
        photo_url=user_dict.get("photo_url"),
    )

    return ParsedInitData(user=user, auth_date=auth_date, raw=pairs)
