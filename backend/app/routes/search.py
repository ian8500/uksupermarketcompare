from __future__ import annotations

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict

from app.services.diagnostics import record_search_event, record_search_quality_event
from app.services.normalization import normalize_product_name
from app.services.search_service import autocomplete_catalog, search_catalog

router = APIRouter()
logger = logging.getLogger(__name__)


class SearchResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    internalProductId: str
    retailerProductId: str | None = None
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
    promoPrice: float | None = None
    image: str | None = None
    availability: str | None = None
    lastUpdated: str | None = None
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
    normalized_query = normalize_product_name(q)
    record_search_event(query=q, normalized_query=normalized_query, result_count=len(ranked), endpoint="/search")
    top_score = ranked[0].score if ranked else 0.0
    record_search_quality_event(
        query=q,
        normalized_query=normalized_query,
        endpoint="/search",
        top_score=top_score,
        weak_match=bool(ranked and top_score < 0.65),
        miss=not ranked,
    )
    logger.info("search endpoint q=%r normalized=%r total=%d", q, normalized_query, len(ranked))
    return SearchResponse(
        query=q,
        normalizedQuery=normalized_query,
        total=len(ranked),
        results=[
            SearchResultItem(
                internalProductId=str(row.item.product_row_id),
                retailerProductId=row.item.source_product_id,
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
                promoPrice=row.item.promo_price,
                image=row.item.image_url,
                availability=row.item.availability,
                lastUpdated=row.item.last_updated,
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
    normalized_query = normalize_product_name(q)
    record_search_event(
        query=q,
        normalized_query=normalized_query,
        result_count=len(suggestions),
        endpoint="/autocomplete",
    )
    top_score = suggestions[0].score if suggestions else 0.0
    record_search_quality_event(
        query=q,
        normalized_query=normalized_query,
        endpoint="/autocomplete",
        top_score=top_score,
        weak_match=bool(suggestions and top_score < 0.65),
        miss=not suggestions,
    )
    logger.info("autocomplete endpoint q=%r normalized=%r total=%d", q, normalized_query, len(suggestions))
    return AutocompleteResponse(query=q, total=len(suggestions), suggestions=suggestions)
