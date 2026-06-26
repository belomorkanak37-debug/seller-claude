from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas.pricing import (
    PromoIn,
    PromoOut,
    RepriceOut,
    RepriceRuleIn,
)
from app.services import pricing as svc
from app.services import products as products_svc

router = APIRouter(prefix="/products", tags=["pricing"])


async def _build_reprice_out(
    session: AsyncSession, product, rule: svc.RepriceRule
) -> RepriceOut:
    prices = await svc.competitor_prices(session, product.id)
    result = svc.compute_reprice(
        float(product.price) if product.price is not None else None, prices, rule
    )
    params = await svc.economics_params(session, product.id)
    be = svc.break_even_price(
        float(product.cost_price or 0), params
    )
    return RepriceOut(
        rule=RepriceRuleIn(
            enabled=rule.enabled,
            undercut_pct=rule.undercut_pct,
            min_price=rule.min_price,
            max_price=rule.max_price,
        ),
        current_price=result.current_price,
        lowest_competitor=result.lowest_competitor,
        target_price=result.target_price,
        recommended_price=result.recommended_price,
        floor=result.floor,
        floor_hit=result.floor_hit,
        would_change=result.would_change,
        direction=result.direction,
        reason=result.reason,
        break_even_price=be,
    )


@router.get("/{product_id}/repricer", response_model=RepriceOut)
async def get_repricer(
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RepriceOut:
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    return await _build_reprice_out(session, product, svc.rule_from_product(product))


@router.put("/{product_id}/repricer", response_model=RepriceOut)
async def save_repricer(
    product_id: int,
    payload: RepriceRuleIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RepriceOut:
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    rule = svc.RepriceRule(
        enabled=payload.enabled,
        undercut_pct=payload.undercut_pct,
        min_price=payload.min_price,
        max_price=payload.max_price,
    )
    await svc.save_rule(session, product, rule)
    return await _build_reprice_out(session, product, rule)


@router.post("/{product_id}/promo-calc", response_model=PromoOut)
async def promo_calc(
    product_id: int,
    payload: PromoIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PromoOut:
    product = await products_svc.get_user_product(session, user.id, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    if not product.price:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "У товара не задана цена"
        )

    params = await svc.economics_params(session, product.id)
    result = svc.compute_promo(
        float(product.price),
        float(product.cost_price or 0),
        params,
        promo_price=payload.promo_price,
        discount_pct=payload.discount_pct,
    )
    return PromoOut(
        base_price=result.base_price,
        promo_price=result.promo_price,
        discount_pct=result.discount_pct,
        net_profit=result.net_profit,
        margin_pct=result.margin_pct,
        is_profitable=result.is_profitable,
        profit_delta=result.profit_delta,
    )
