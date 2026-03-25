from typing import Literal
from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    title: str
    url: str
    body: str
    source: str
    published_at: str


class RiskItem(BaseModel):
    headline: str
    source: str
    peril_type: Literal["nat-cat", "cyber", "liability", "market", "operational"]
    severity: int = Field(ge=1, le=5)
    region: str
    summary: str
    published_at: str


class RiskSummaryReport(BaseModel):
    date: str
    total_signals: int
    high_severity_count: int
    peril_breakdown: dict[str, int]
    executive_summary: str
    top_risks: list[RiskItem]


class RiskItemBatch(BaseModel):
    items: list[RiskItem]
