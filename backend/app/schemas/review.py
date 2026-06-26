from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    external_id: str | None = None
    source: str
    author: str | None = None
    text: str | None = None
    rating: float | None = None
    published_at: datetime | None = None
    sentiment: str | None = None
