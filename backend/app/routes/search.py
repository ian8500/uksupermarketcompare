from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict

from app.services.normalization import normalize_product_name
from app.services.search_service import autocomplete_catalog, search_catalog

router = APIRouter()


class SearchResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supermarket: str
    supermarketDescription: str
    name: str
    canonicalName: str
    brand: str
    size: str
    category: str
    subcategory: str
    tags: list[str]
    price: float
    unitDescription: str
    unitValue: float
    score: float
    matchType: str
    matchedTerms: list[str]


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    normalizedQuery: str
    total: int
    results: list[SearchResultItem]


class AutocompleteSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggestion: str
    displayName: str
    brand: str
    size: str
    category: str
    score: float
    matchType: str


class AutocompleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    total: int
    suggestions: list[AutocompleteSuggestion]


@router.get("/search", response_model=SearchResponse)
def search(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=50)) -> SearchResponse:
    ranked = search_catalog(q, limit=limit)
    return SearchResponse(
        query=q,
        normalizedQuery=normalize_product_name(q),
        total=len(ranked),
        results=[
            SearchResultItem(
                supermarket=row.item.retailer,
                supermarketDescription=row.item.retailer_description,
                name=row.item.product_name,
                canonicalName=row.item.canonical_name,
                brand=row.item.brand,
                size=row.item.size,
                category=row.item.category,
                subcategory=row.item.subcategory,
                tags=row.item.tags,
                price=row.item.price,
                unitDescription=row.item.unit_description,
                unitValue=row.item.unit_value,
                score=row.score,
                matchType=row.match_type,
                matchedTerms=row.matched_terms,
            )
            for row in ranked
        ],
    )


@router.get("/autocomplete", response_model=AutocompleteResponse)
def autocomplete(q: str = Query(..., min_length=1), limit: int = Query(8, ge=1, le=20)) -> AutocompleteResponse:
    suggestions = [AutocompleteSuggestion(**item) for item in autocomplete_catalog(q, limit=limit)]
    return AutocompleteResponse(query=q, total=len(suggestions), suggestions=suggestions)
