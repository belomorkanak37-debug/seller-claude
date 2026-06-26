"""Фикстуры для интеграционных тестов API на in-memory SQLite + фейк-провайдер."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.services.competitors as comp_svc
import app.services.products as svc
from app.api.deps import get_current_user
from app.db.base import Base
from app.db.models import User
from app.db.session import get_session
from app.main import app
from app.providers.base import (
    CompetitorDTO,
    Marketplace,
    ProductDTO,
    ReviewDTO,
)


class FakeWildberriesProvider:
    """Фейковый провайдер: отдаёт детерминированные данные без сети."""

    marketplace = Marketplace.WILDBERRIES

    async def get_product(self, article: str) -> ProductDTO:
        return ProductDTO(
            marketplace=Marketplace.WILDBERRIES,
            article=article,
            name="Комод белый 4 ящика",
            price=3499.0,
            photo_url="https://img/1.webp",
            rating=4.7,
            reviews_count=2,
            tags=["Цвет: белый", "Материал: ЛДСП"],
            stock=15,
            root_id="999",
            brand="ИКЕА",
        )

    async def get_reviews(self, product_id: str, limit: int = 50):
        return [
            ReviewDTO(
                external_id="r1",
                author="Анна",
                text="отличный комод",
                rating=5,
                published_at=datetime(2026, 1, 2),
                source="wildberries",
            )
        ]

    async def search_competitors(self, keywords, limit: int = 10):
        # один из результатов совпадает с собственным товаром (article=123)
        return [
            CompetitorDTO(
                marketplace=Marketplace.WILDBERRIES,
                article="555",
                name="Комод дубовый конкурент",
                price=4100.0,
                photo_url="https://img/c.webp",
                rating=4.5,
                reviews_count=88,
                url="https://www.wildberries.ru/catalog/555/detail.aspx",
            ),
            CompetitorDTO(
                marketplace=Marketplace.WILDBERRIES,
                article="123",
                name="Это мой товар",
                price=3499.0,
            ),
        ]


@pytest.fixture()
def client(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    Session = async_sessionmaker(engine, expire_on_commit=False)

    import asyncio

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with Session() as s:
            s.add(User(telegram_id=42, first_name="Test"))
            await s.commit()

    asyncio.get_event_loop().run_until_complete(setup())

    async def override_session():
        async with Session() as s:
            yield s

    async def override_user():
        async with Session() as s:
            return (await s.execute(select(User))).scalars().first()

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user] = override_user
    fake = lambda mp: FakeWildberriesProvider()  # noqa: E731
    monkeypatch.setattr(svc, "get_provider", fake)
    monkeypatch.setattr(comp_svc, "get_provider", fake)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    asyncio.get_event_loop().run_until_complete(engine.dispose())
