from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas.cards import (
    CardComparisonOut,
    CardMetricsOut,
    PositionItem,
    PositionPoint,
    PositionSeries,
    PositionsOut,
    SeoOut,
    TrackedQueriesIn,
)
from app.services import cards as cards_svc
from app.services import competitors as competitors_svc
from app.services import positions as positions_svc
from app.services import products as products_svc

router = APIRouter(prefix="/products", tags=["cards"])


async def _require_product(session, user_id, product_id):
    product = await products_svc.get_user_product(session, user_id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    return product


@router.get("/{product_id}/positions", response_model=PositionsOut)
async def get_positions(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PositionsOut:
    product = await _require_product(session, user.id, product_id)
    history = await positions_svc.get_history(session, product_id)
    latest = [
        PositionItem(query=q, position=points[-1]["position"])
        for q, points in history.items()
        if points
    ]
    return PositionsOut(
        queries=positions_svc.get_queries(product),
        latest=latest,
        history=[
            PositionSeries(
                query=q,
                points=[PositionPoint(**p) for p in points],
            )
            for q, points in history.items()
        ],
    )


@router.post("/{product_id}/positions/check", response_model=list[PositionItem])
async def check_positions(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[PositionItem]:
    """Живая проверка позиций + сохранение снапшота."""
    product = await _require_product(session, user.id, product_id)
    result = await positions_svc.check_positions(session, product, store=True)
    return [PositionItem(**r) for r in result]


@router.put("/{product_id}/tracked-queries", response_model=PositionsOut)
async def set_tracked_queries(
    product_id: int,
    payload: TrackedQueriesIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PositionsOut:
    product = await _require_product(session, user.id, product_id)
    cleaned = [q.strip() for q in payload.queries if q.strip()]
    product.tracked_queries = cleaned or None
    await session.commit()
    history = await positions_svc.get_history(session, product_id)
    return PositionsOut(
        queries=positions_svc.get_queries(product),
        latest=[
            PositionItem(query=q, position=points[-1]["position"])
            for q, points in history.items()
            if points
        ],
        history=[
            PositionSeries(query=q, points=[PositionPoint(**p) for p in points])
            for q, points in history.items()
        ],
    )


@router.get("/{product_id}/card-comparison", response_model=CardComparisonOut)
async def card_comparison(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CardComparisonOut:
    product = await _require_product(session, user.id, product_id)
    competitors = await competitors_svc.list_competitors(session, product_id)
    cmp = cards_svc.compare_cards(product, competitors)
    return CardComparisonOut(
        product=CardMetricsOut(**cmp.product.__dict__),
        competitors_avg=cmp.competitors_avg,
        recommendations=cmp.recommendations,
    )


@router.get("/{product_id}/seo", response_model=SeoOut)
async def seo(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SeoOut:
    product = await _require_product(session, user.id, product_id)
    competitors = await competitors_svc.list_competitors(session, product_id)
    result = cards_svc.build_seo(product, competitors)
    return SeoOut(
        suggested_keywords=result.suggested_keywords,
        score=result.score,
        tips=result.tips,
    )
