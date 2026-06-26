# Помощник продавца на маркетплейсах (Telegram Mini App)

Telegram Mini App + бот — помощник продавца на **Ozon, Wildberries, Яндекс Маркет**.
Продавец добавляет товар по артикулу, получает карточку, конкурентов, цены,
рейтинги, отзывы, историю цен и аналитику. Все данные — реальные.

> Статус: **Этап 3 — конкуренты** (готово). Этапы 0–2 — готовы.

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

## Этап 1 — свой товар на реальных данных

Добавление товара по артикулу на **реальных данных Wildberries** (публичные JSON
WB: карточка, цена, рейтинг, остаток, отзывы, характеристики). Ozon и Яндекс
Маркет дают понятную ошибку «подключаются на Этапе 2» — без фейковых данных.

### Провайдеры
- `backend/app/providers/wildberries.py` — реализация `MarketplaceProvider` на
  httpx (карточка `card.wb.ru`, характеристики `basket.../card.json`, отзывы
  `feedbacks{1,2}.wb.ru`, поиск `search.wb.ru`). Ретраи + backoff в
  `providers/http.py`.
- `providers/stubs.py` — Ozon / Я.Маркет: `SourceUnavailable` с пояснением.
- `providers/registry.py` — фабрика `get_provider(marketplace)`.

### API (все требуют `Authorization: tma <initData>`)
| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/products/lookup?marketplace=&article=` | живая карточка + отзывы для «Это ваш товар?» |
| POST | `/products` | подтвердить: сервер заново тянет данные и сохраняет товар + отзывы |
| GET | `/products` | список моих товаров |
| GET | `/products/{id}` | карточка товара |
| GET | `/products/{id}/reviews` | сохранённые отзывы |
| PATCH | `/products/{id}` | редактировать любые поля |
| DELETE | `/products/{id}` | удалить |

### Mini App (экраны)
Список товаров → «Добавить» → ввод артикула и маркетплейса → экран
**«Это ваш товар?»** (фото, цена, рейтинг, реальные отзывы, теги) →
подтверждение → карточка товара → **редактирование** любых полей.

### Что проверить
1. В Mini App «Добавить» → Wildberries → реальный артикул WB → «Найти товар».
2. Появляется карточка с реальными названием/фото/ценой/рейтингом/отзывами/тегами.
3. «Это мой товар» → товар сохранён, открывается его карточка; есть в списке.
4. «Редактировать» → меняем любое поле (цена, остаток, себестоимость, заметка,
   теги) → сохраняется.
5. Несуществующий артикул → понятная ошибка «Товар не найден».
6. Ozon / Я.Маркет → сообщение, что площадка подключается на Этапе 2.

> Примечание: WB отдаёт данные только по «живым» IP. С дата-центровых адресов
> возможен ответ `403` — это снимается слоем резидентных прокси на Этапе 2.
> Код устойчив к этому: ошибка источника возвращается как понятный 502, не падает.

### Тесты
```bash
cd backend
pip install -r requirements-dev.txt
pytest -q          # 13 тестов: парсинг WB + поток lookup/create/list/edit/delete
```

## Этап 2 — парсинг-фундамент

Слой устойчивого парсинга и провайдеры для всех трёх площадок за единым
интерфейсом `MarketplaceProvider`.

### Слой устойчивости (`backend/app/scraping/`)
- **`proxy.py`** — `ProxyPool`: режим ротирующего шлюза (`PROXY_URL`, рекомендуемый)
  или список прокси (`PROXY_LIST`) с round-robin и cooldown при бане.
- **`throttle.py`** — троттлинг по хосту: минимальный интервал + случайная пауза.
- **`captcha.py`** — абстракция `CaptchaSolver` + адаптер **2captcha/rucaptcha**
  (переключается `CAPTCHA_BASE_URL`). Без ключа — `NoCaptchaSolver` с понятной ошибкой.
- **`browser.py`** — headless-Chromium (Playwright) со stealth-настройками
  (UA, locale ru-RU, timezone, маскировка `webdriver`), прокси, перехват JSON-ответов,
  детект капчи/блокировки.
- **`cache.py`** — кеш результатов парсинга в Redis с TTL (`PROVIDER_CACHE_TTL`),
  прозрачно отключается при недоступности Redis.
- **`parsers.py`** — чистые функции: `ld+json` (schema.org/Product) и
  Ozon `composer-api` widgetStates. Устойчивы к смене вёрстки, покрыты тестами.

### Провайдеры
- **Wildberries** — httpx + публичные JSON (как на Этапе 1), теперь с
  троттлингом, прокси и Redis-кешем.
- **Ozon** — Playwright: рендер карточки, парсинг из перехваченного `composer-api`
  JSON (fallback — `ld+json`).
- **Яндекс Маркет** — Playwright: парсинг из `ld+json` (устойчиво к SmartCaptcha-вёрстке).

### Очереди (`backend/app/workers/`) — Celery + Redis
- `celery_app.py` — Celery на Redis, beat-расписание.
- `tasks.py` — `refresh_product(id)` (обновить карточку), `snapshot_all_prices()`
  (ежедневный снимок цен, beat 03:00 — основа Этапа 5).
- Сервисы `worker` и `beat` в docker-compose.

### Конфигурация (.env)
`PROXY_URL` / `PROXY_LIST`, `CAPTCHA_PROVIDER` / `CAPTCHA_API_KEY` / `CAPTCHA_BASE_URL`,
`PROVIDER_CACHE_TTL`, `THROTTLE_MIN_INTERVAL` / `THROTTLE_JITTER`,
`PLAYWRIGHT_HEADLESS` / `PLAYWRIGHT_NAV_TIMEOUT_MS`. См. `.env.example`.

### Что проверить
1. `docker compose up` поднимает дополнительно `worker` и `beat` (Celery).
2. WB-товар добавляется как раньше; повторный lookup того же артикула берётся
   из Redis-кеша (нет повторного запроса к WB в пределах TTL).
3. Без прокси Ozon/Я.Маркет с дата-центрового IP вернут капчу/блок — приходит
   понятная ошибка (нужны резидентные прокси + ключ капчи).
4. `celery -A app.workers.celery_app worker` стартует, задачи зарегистрированы.

### Тесты
```bash
cd backend && pip install -r requirements-dev.txt && pytest -q   # 28 passed
```
Покрыто: ротация/cooldown прокси, троттлинг, кеш (fake-redis), выбор решателя
капчи, парсинг `ld+json` и Ozon `composer-api`, плюс поток Этапа 1.

> Playwright-навигация Ozon/Я.Маркет требует реального браузера, прокси и (часто)
> решателя капчи — её парсеры вынесены в чистые функции и протестированы на
> сэмплах ответов. Прогон против живых Ozon/Я.Маркет выполняется в среде заказчика
> с резидентными прокси.

## Этап 3 — конкуренты

Поиск конкурентов по ключевым словам названия и работа с ними на реальных данных.

### Логика
- **Ключевые слова** (`services/keywords.py`): из названия товара выделяются 2–4
  значимых слова (категория + свойство), стоп-слова, числа и размеры
  отбрасываются. Поиск ведётся по ним, а не по полному названию.
- **Поиск** (`services/competitors.py`): `provider.search_competitors(keywords)`
  на той же площадке; собственный товар исключается из выдачи.
- **Добавление**: при сохранении конкурента best-effort подтягиваются его
  **реальные теги и отзывы** (`get_product` + `get_reviews`).
- **Заметка**: у конкурента есть поле `note` для записей продавца. Никакой
  заглушки «Добавить отзыв» — только реальные отзывы конкурента со страницы.

### Поиск по площадкам
- Wildberries — `search.wb.ru` (публичный JSON).
- Ozon / Яндекс Маркет — рендер страницы поиска (Playwright) + парсинг
  `ld+json ItemList` (устойчиво к вёрстке); при блокировке — понятная ошибка.

### API
| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/products/{id}/competitors/search` | ключевые слова + найденные конкуренты |
| POST | `/products/{id}/competitors` | добавить конкурента (+теги/отзывы) |
| GET | `/products/{id}/competitors` | список конкурентов товара |
| GET | `/competitors/{cid}/reviews` | реальные отзывы конкурента |
| PATCH | `/competitors/{cid}` | заметка/поля конкурента |
| DELETE | `/competitors/{cid}` | удалить |

### Mini App
В карточке товара — кнопка **«Конкуренты»**: показывает выделенные ключевые
слова, найденных конкурентов с кнопкой «Добавить», список добавленных
конкурентов с **полем «Заметка»**, реальными тегами и разворачиваемыми
**отзывами конкурента**.

### Что проверить
1. Открыть товар → «Конкуренты»: видны ключевые слова (напр. «комод», «белый»).
2. В выдаче — реальные карточки конкурентов (фото, цена, рейтинг); своего товара нет.
3. «Добавить» → конкурент в списке с тегами и отзывами; «Заметка» сохраняется.

### Тесты
```bash
cd backend && pip install -r requirements-dev.txt && pytest -q   # 40 passed
```
Добавлено: извлечение ключевых слов, парсинг `ld+json ItemList`, поток
поиск→добавление→отзывы→заметка→удаление.

## Дальше по плану

Этап 4 — отзывы и уведомления: реальные отзывы по моему товару, периодическая
проверка новых отзывов и уведомление в бот, настройки уведомлений.
```
