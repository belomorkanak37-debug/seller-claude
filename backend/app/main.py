from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    competitors,
    health,
    price_history,
    products,
    users,
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


@app.get("/")
async def root() -> dict:
    return {"service": "seller-assistant", "status": "ok"}
