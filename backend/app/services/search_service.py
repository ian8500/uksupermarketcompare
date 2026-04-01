from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass

from app.db import get_connection
from app.services.normalization import normalize_product_name, normalize_size, normalize_text
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchCandidate:
    retailer: str
    retailer_description: str
    product_name: str
    brand: str
    size: str
    subcategory: str
    category: str
    tags: list[str]
    price: float
    unit_description: str
    unit_value: float
    raw_searchable_text: str
    canonical_name: str
    canonical_searchable_text: str
    mapping_confidence: float


@dataclass(frozen=True)
class RankedSearchResult:
    item: SearchCandidate
    score: float
    match_type: str
    matched_terms: list[str]


def _latest_catalog_candidates() -> list[SearchCandidate]:
    with get_connection() as conn:
        unmapped_count = conn.execute(
            "SELECT COUNT(*) AS count FROM raw_retailer_products raw LEFT JOIN product_mappings pm ON pm.raw_product_id = raw.id WHERE pm.id IS NULL"
        ).fetchone()["count"]
        if unmapped_count:
            logger.warning("Detected failed mappings raw_products_without_mapping=%d", unmapped_count)
        rows = conn.execute(
            """
            SELECT
              r.name AS retailer_name,
              r.description AS retailer_description,
              raw.source_name,
              raw.source_brand,
              raw.source_size,
              raw.source_subcategory,
              raw.searchable_text AS raw_searchable_text,
              cp.canonical_name,
              cp.category,
              cp.tags,
              cp.searchable_text AS canonical_searchable_text,
              pm.confidence AS mapping_confidence,
              ps.price,
              ps.unit_description,
              ps.unit_value
            FROM raw_retailer_products raw
            JOIN retailers r ON r.id = raw.retailer_id
            JOIN product_mappings pm ON pm.raw_product_id = raw.id
            JOIN canonical_products cp ON cp.id = pm.canonical_product_id
            JOIN (
                SELECT raw_product_id, MAX(captured_at) AS latest_time
                FROM price_snapshots
                GROUP BY raw_product_id
            ) latest ON latest.raw_product_id = raw.id
            JOIN price_snapshots ps ON ps.raw_product_id = raw.id AND ps.captured_at = latest.latest_time
            ORDER BY r.name, raw.source_name
            """
        ).fetchall()

    return [
        SearchCandidate(
            retailer=row["retailer_name"],
            retailer_description=row["retailer_description"],
            product_name=row["source_name"],
            brand=row["source_brand"],
            size=row["source_size"],
            subcategory=row["source_subcategory"],
            category=row["category"],
            tags=[tag for tag in row["tags"].split(",") if tag],
            price=float(row["price"]),
            unit_description=row["unit_description"],
            unit_value=float(row["unit_value"]),
            raw_searchable_text=row["raw_searchable_text"],
            canonical_name=row["canonical_name"],
            canonical_searchable_text=row["canonical_searchable_text"],
            mapping_confidence=float(row["mapping_confidence"]),
        )
        for row in rows
    ]


def _synonym_map() -> dict[str, str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT synonym, canonical_term FROM search_synonyms").fetchall()
    return {normalize_text(row["synonym"]): normalize_text(row["canonical_term"]) for row in rows}


def _expand_terms(query: str) -> tuple[str, list[str], list[str], list[str]]:
    normalized_query = normalize_product_name(query, synonyms=_synonym_map())
    raw_tokens = [token for token in normalize_text(query).split() if token]
    expanded_tokens = [token for token in normalized_query.split() if token]

    size = normalize_size(query)
    size_terms: list[str] = []
    if size.normalized_value is not None and size.normalized_unit:
        size_value = int(size.normalized_value) if float(size.normalized_value).is_integer() else size.normalized_value
        size_terms.append(f"{size_value}{size.normalized_unit}")
    return normalized_query, raw_tokens, expanded_tokens, size_terms


def _score_candidate(candidate: SearchCandidate, normalized_query: str, expanded_tokens: list[str], size_terms: list[str]) -> RankedSearchResult | None:
    query_text = normalized_query.strip()
    if not query_text:
        return None

    haystack = f"{candidate.raw_searchable_text} {candidate.canonical_searchable_text}"
    score = 0.0
    matched_terms: list[str] = []
    match_type = "fuzzy"

    if query_text == normalize_text(candidate.product_name) or query_text == normalize_text(candidate.canonical_name):
        score += 1.0
        match_type = "exact"
        matched_terms.append(query_text)

    if query_text in haystack:
        score += 0.6
        if match_type != "exact":
            match_type = "partial"
        matched_terms.append(query_text)

    token_matches = [token for token in expanded_tokens if token in haystack]
    if token_matches:
        token_score = 0.12 * len(token_matches)
        score += min(token_score, 0.48)
        matched_terms.extend(token_matches)

    brand_token = normalize_text(candidate.brand)
    brand_hits = [token for token in expanded_tokens if token in brand_token]
    if brand_hits:
        score += 0.25
        if match_type == "fuzzy":
            match_type = "brand"
        matched_terms.extend(brand_hits)

    if size_terms and any(size_term in haystack for size_term in size_terms):
        score += 0.22
        if match_type == "fuzzy":
            match_type = "size"
        matched_terms.extend(size_terms)

    fuzzy_candidates = [
        normalize_text(candidate.product_name),
        normalize_text(candidate.canonical_name),
        candidate.raw_searchable_text,
    ]
    fuzzy_ratio = max(difflib.SequenceMatcher(a=query_text, b=text).ratio() for text in fuzzy_candidates if text)
    if fuzzy_ratio >= 0.62:
        score += fuzzy_ratio * 0.45
        if match_type == "fuzzy":
            match_type = "fuzzy"

    if score < 0.4:
        return None

    final_score = min(score * (0.8 + (0.2 * candidate.mapping_confidence)), 1.0)
    unique_terms = sorted(set(matched_terms))
    return RankedSearchResult(item=candidate, score=round(final_score, 4), match_type=match_type, matched_terms=unique_terms)


def search_catalog(query: str, limit: int = 20) -> list[RankedSearchResult]:
    normalized_query, _raw_tokens, expanded_tokens, size_terms = _expand_terms(query)
    ranked = [
        ranked_row
        for candidate in _latest_catalog_candidates()
        if (ranked_row := _score_candidate(candidate, normalized_query, expanded_tokens, size_terms)) is not None
    ]
    ranked.sort(key=lambda row: (row.score, -row.item.price), reverse=True)
    sliced = ranked[: max(1, min(limit, 50))]
    logger.info(
        "search query=%r normalized=%r results=%d limit=%d",
        query,
        normalized_query,
        len(sliced),
        limit,
    )
    if not sliced:
        logger.warning("search_miss query=%r normalized=%r", query, normalized_query)
    return sliced


def autocomplete_catalog(query: str, limit: int = 8) -> list[dict[str, str | float]]:
    ranked = search_catalog(query, limit=max(limit * 3, 10))
    suggestions: list[dict[str, str | float]] = []
    seen: set[str] = set()

    for row in ranked:
        canonical_key = normalize_text(row.item.canonical_name)
        if canonical_key in seen:
            continue
        seen.add(canonical_key)

        suggestions.append(
            {
                "suggestion": row.item.canonical_name,
                "displayName": row.item.product_name,
                "brand": row.item.brand,
                "size": row.item.size,
                "category": row.item.category,
                "score": row.score,
                "matchType": row.match_type,
            }
        )

        if len(suggestions) >= max(1, min(limit, 20)):
            break

    logger.info("autocomplete query=%r suggestions=%d limit=%d", query, len(suggestions), limit)
    if not suggestions:
        logger.warning("autocomplete_miss query=%r", query)
    return suggestions
