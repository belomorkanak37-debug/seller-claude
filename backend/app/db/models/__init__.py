"""Импорт всех моделей, чтобы Alembic и SQLAlchemy видели их в metadata."""

from app.db.models.ad_stat import AdStat
from app.db.models.competitor import Competitor
from app.db.models.notification import Notification
from app.db.models.payout import Payout
from app.db.models.position_snapshot import PositionSnapshot
from app.db.models.price_snapshot import PriceSnapshot
from app.db.models.product import Product
from app.db.models.review import Review
from app.db.models.unit_economics import UnitEconomics
from app.db.models.user import User

__all__ = [
    "User",
    "Product",
    "Competitor",
    "Review",
    "PriceSnapshot",
    "PositionSnapshot",
    "Notification",
    "UnitEconomics",
    "AdStat",
    "Payout",
]
