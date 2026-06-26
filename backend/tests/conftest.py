"""Фикстуры для тестов на in-memory SQLite + фейк-провайдер (без сети)."""

import asyncio
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.services.competitors as comp_svc
import app.services.positions as positions_svc
import app.services.price_history as price_svc
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


def _review(external_id: str, author: str, text: str, rating: float) -> ReviewDTO:
    return ReviewDTO(
        external_id=external_id,
        author=author,
        text=text,
        rating=rating,
        published_at=datetime(2026, 1, 2),
        source="wildberries",
    )


class FakeWildberriesProvider:
    """Фейковый провайдер: детерминированные данные без сети."""

    marketplace = Marketplace.WILDBERRIES
    # Дополнительные отзывы, которые тест может «подбросить» как новые.
    EXTRA_REVIEWS: list[ReviewDTO] = []

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
        base = [_review("r1", "Анна", "отличный комод", 5)]
        return base + list(FakeWildberriesProvider.EXTRA_REVIEWS)

    # Текущая цена (для снапшотов истории цен)
    PRICE: float = 3499.0
    STOCK: int = 10

    async def get_price(self, product_id: str):
        return FakeWildberriesProvider.PRICE

    async def get_stock(self, product_id: str):
        return FakeWildberriesProvider.STOCK

    async def search_competitors(self, keywords, limit: int = 10):
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


def _make_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with Session() as s:
            s.add(User(telegram_id=42, first_name="Test"))
            await s.commit()

    asyncio.get_event_loop().run_until_complete(setup())
    return engine, Session


@pytest.fixture(autouse=True)
def _reset_fake():
    FakeWildberriesProvider.EXTRA_REVIEWS = []
    FakeWildberriesProvider.PRICE = 3499.0
    FakeWildberriesProvider.STOCK = 10
    yield
    FakeWildberriesProvider.EXTRA_REVIEWS = []
    FakeWildberriesProvider.PRICE = 3499.0
    FakeWildberriesProvider.STOCK = 10


@pytest.fixture()
def client(monkeypatch):
    engine, Session = _make_env()

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
    monkeypatch.setattr(price_svc, "get_provider", fake)
    monkeypatch.setattr(positions_svc, "get_provider", fake)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.fixture()
def db(monkeypatch):
    """Прямой доступ к сессии и id пользователя для сервис-тестов."""
    engine, Session = _make_env()
    fake = lambda mp: FakeWildberriesProvider()  # noqa: E731
    monkeypatch.setattr(svc, "get_provider", fake)
    monkeypatch.setattr(comp_svc, "get_provider", fake)
    monkeypatch.setattr(price_svc, "get_provider", fake)
    monkeypatch.setattr(positions_svc, "get_provider", fake)
    yield Session
    asyncio.get_event_loop().run_until_complete(engine.dispose())
