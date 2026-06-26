from pydantic import BaseModel, Field


class ReplyOut(BaseModel):
    reply: str


class SentimentOut(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0


class ReviewAnalysisOut(BaseModel):
    sentiment: SentimentOut
    common_complaints: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class CompetitorAnalysisOut(BaseModel):
    praise: list[str] = Field(default_factory=list)
    criticism: list[str] = Field(default_factory=list)
    differentiation: list[str] = Field(default_factory=list)
