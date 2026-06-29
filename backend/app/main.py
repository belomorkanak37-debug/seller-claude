from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    advertising,
    ai,
    auth,
    cards,
    competitors,
    finance,
    health,
    price_history,
    pricing,
    products,
    unit_economics,
    users,
    warehouse,
)
from app.config import settings

app = FastAPI(title="Seller Assistant API", version="0.1.0")

# CORS для Mini App (домен из туннеля). Если список пуст — разрешаем всё в dev.
allow_origins = settings.cors_origins_list or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(competitors.router)
app.include_router(users.router)
app.include_router(price_history.router)
app.include_router(unit_economics.router)
app.include_router(warehouse.router)
app.include_router(pricing.router)
app.include_router(cards.router)
app.include_router(ai.router)
app.include_router(advertising.router)
app.include_router(finance.router)


@app.get("/")
async def root() -> dict:
    return {"service": "seller-assistant", "status": "ok"}
