from typing import Literal

from pydantic import BaseModel, Field


class ListParseRequest(BaseModel):
    text: str = Field(..., min_length=2)


class ParsedItem(BaseModel):
    text: str
    quantity: int = 1


class ListParseResponse(BaseModel):
    items: list[ParsedItem]


class BasketCompareRequest(BaseModel):
    items: list[str]
    retailers: list[str]


class MatchedProduct(BaseModel):
    product_name: str
    supermarket: str
    price: float
    unit_price: float | None
    size: str | None
    brand: str | None
    own_brand: bool
    confidence: Literal["exact", "close", "substitute"]
    confidence_score: float
    uncertainty: str | None = None


class CompareItemResult(BaseModel):
    query: str
    matches: list[MatchedProduct]


class BasketCompareResponse(BaseModel):
    basket_id: int
    results: list[CompareItemResult]
    cheapest_overall_basket: float
    cheapest_single_store_basket: dict[str, float]
    own_brand_savings: float


class SavedListIn(BaseModel):
    name: str
    items: list[str]
    user_id: int | None = None


class SavedListOut(BaseModel):
    id: int
    name: str
    items: list[str]
