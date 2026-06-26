"""Celery-приложение: брокер и backend — Redis. Расписание через beat.

Фоновые/периодические задачи парсинга вынесены сюда, чтобы не блокировать API
и держать единый троттлинг/кеш. Запуск:
  celery -A app.workers.celery_app worker --loglevel=info
  celery -A app.workers.celery_app beat   --loglevel=info
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "seller",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
)

# Периодические задачи. Снимок цен — раз в сутки (используется на Этапе 5).
celery_app.conf.beat_schedule = {
    "daily-price-snapshots": {
        "task": "app.workers.tasks.snapshot_all_prices",
        "schedule": crontab(hour=3, minute=0),
    },
}
