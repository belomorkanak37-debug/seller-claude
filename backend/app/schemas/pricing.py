from pydantic import BaseModel, Field, model_validator


class RepriceRuleIn(BaseModel):
    enabled: bool = False
    undercut_pct: float = Field(0, ge=0)
    min_price: float | None = Field(None, ge=0)
    max_price: float | None = Field(None, ge=0)


class RepriceOut(BaseModel):
    rule: RepriceRuleIn
    current_price: float | None = None
    lowest_competitor: float | None = None
    target_price: float | None = None
    recommended_price: float | None = None
    floor: float | None = None
    floor_hit: bool
    would_change: bool
    direction: str
    reason: str
    break_even_price: float | None = None


class PromoIn(BaseModel):
    promo_price: float | None = Field(None, ge=0)
    discount_pct: float | None = Field(None, ge=0, le=100)

    @model_validator(mode="after")
    def _one_of(self):
        if self.promo_price is None and self.discount_pct is None:
            raise ValueError("Укажите promo_price или discount_pct")
        return self


class PromoOut(BaseModel):
    base_price: float
    promo_price: float
    discount_pct: float
    net_profit: float
    margin_pct: float | None = None
    is_profitable: bool
    profit_delta: float
