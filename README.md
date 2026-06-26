# Помощник продавца на маркетплейсах (Telegram Mini App)

Telegram Mini App + бот — помощник продавца на **Ozon, Wildberries, Яндекс Маркет**.
Продавец добавляет товар по артикулу, получает карточку, конкурентов, цены,
рейтинги, отзывы, историю цен и аналитику. Все данные — реальные.

> Статус: **Этап 0 — каркас и инфраструктура** (готово).

## Стек

| Слой        | Технологии                                                        |
|-------------|-------------------------------------------------------------------|
| Frontend    | React + Vite + TypeScript, Tailwind CSS, shadcn/ui, Telegram WebApp SDK |
| Backend     | Python, FastAPI, SQLAlchemy (async), Pydantic, Alembic            |
| Бот         | Python, aiogram 3.x (polling)                                     |
| БД / кеш    | PostgreSQL, Redis                                                 |
| Инфра       | Docker + docker-compose                                          |

## Архитектура

```
Telegram Bot (aiogram, polling) ──► кнопка «Открыть приложение» (Mini App)
        │                                   │
        │ уведомления                       │ запускает WebView (React)
        ▼                                   ▼
   Backend API (FastAPI)  ◄─────────────────┘  (авторизация по initData)
        ├── PostgreSQL  (users, products, competitors, reviews, price_snapshots, ...)
        ├── Redis       (кеш, очереди Celery — со следующих этапов)
        └── Провайдеры данных (Ozon / WB / Я.Маркет — со Этапа 2)
```

Ключевой принцип — абстракция **`MarketplaceProvider`** (`backend/app/providers/base.py`):
единый интерфейс `get_product / search_competitors / get_reviews / get_price /
get_tags / get_stock`. Способ получения данных (публичный эндпоинт или парсинг)
скрыт за интерфейсом. Реализации провайдеров появятся на Этапе 2.

## Структура проекта

```
seller-claude/
├── docker-compose.yml
├── .env.example
├── backend/        # FastAPI API, модели, миграции, провайдеры
├── bot/            # Telegram-бот (aiogram, polling)
└── frontend/       # React Mini App (nginx + прокси /api -> backend)
```

## Предварительные требования

- Docker + docker-compose
- Telegram-бот: токен от [@BotFather](https://t.me/BotFather)
- Туннель для публичного HTTPS — **cloudflared** (Telegram открывает Mini App только по HTTPS)

## Запуск (Этап 0)

### 1. Переменные окружения

```bash
cp .env.example .env
```

В `.env` заполни:
- `BOT_TOKEN` — токен от @BotFather;
- `WEBAPP_URL` — публичный HTTPS-URL фронта (получим на шаге 3);
- `CORS_ORIGINS` — тот же домен, что и `WEBAPP_URL` (на всякий случай; основной путь — через nginx-прокси, CORS не задействуется).

### 2. Поднять сервисы

```bash
docker compose up --build
```

Поднимутся: `db` (Postgres), `redis`, `backend` (миграции Alembic + FastAPI на :8000),
`bot` (polling), `frontend` (nginx на :5173).

Проверка API:
```bash
curl http://localhost:8000/health      # {"status":"ok","db":true}
```

### 3. Публичный туннель (cloudflared)

Mini App должен открываться по HTTPS. Запусти быстрый туннель на фронт:

```bash
cloudflared tunnel --url http://localhost:5173
```

Cloudflared выдаст адрес вида `https://<random>.trycloudflare.com`.
Впиши его в `.env` → `WEBAPP_URL` (и `CORS_ORIGINS`), затем перезапусти бота:

```bash
docker compose up -d --force-recreate bot
```

> Бэкенд проксируется через nginx по пути `/api`, поэтому отдельный туннель для
> API не нужен — фронт и API на одном домене.

### 4. Привязать Mini App к боту (опционально, но удобно)

В @BotFather → `/setmenubutton` или через `/newapp` укажи тот же `WEBAPP_URL`.
Бот и так выставляет кнопку-меню и присылает inline-кнопку при `/start`.

## Что проверить (критерии Этапа 0)

1. `docker compose up` поднимает все сервисы, `GET /health` отвечает `db: true`.
2. В Telegram команда **`/start`** → сообщение с кнопкой **«Открыть приложение»**
   и кнопка-меню рядом с полем ввода.
3. Нажатие открывает **Mini App в WebView**: применяется тема Telegram,
   работает нативный **BackButton**, срабатывают **хаптики**.
4. На старте фронт отправляет `initData` на `POST /api/auth/telegram`.
   Бэкенд **валидирует HMAC-подпись** (от `BOT_TOKEN`), создаёт/находит
   пользователя по `telegram_id`. На экране — «Авторизация подтверждена»
   с именем и telegram_id. Для нового пользователя — пометка «создан только что».
5. В таблице `users` появляется запись:
   ```bash
   docker compose exec db psql -U seller -d seller -c "select id, telegram_id, username from users;"
   ```

## Безопасность

- `initData` валидируется **на сервере** (HMAC-SHA256, `WebAppData`-ключ от
  токена бота) — фронту на слово не верим. См. `backend/app/core/telegram_auth.py`.
- Защищённые эндпоинты (со следующих этапов) читают `initData` из заголовка
  `Authorization: tma <initData>` через зависимость `get_current_user`.
- Секреты только в `.env` (в `.gitignore`), не логируются.

## Дальше по плану

Этап 1 — добавление своего товара по артикулу на реальных данных
(карточка, фото, цена, рейтинг, отзывы, теги) + подтверждение и редактирование.
```
