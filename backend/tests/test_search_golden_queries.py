from app.db import init_db
from app.routes.search import autocomplete, search
from app.services.catalog_store import ensure_seed_data


init_db()
ensure_seed_data()


def _assert_search_contract(payload) -> None:
    data = payload.model_dump(mode="json")
    assert set(data.keys()) == {"query", "normalizedQuery", "total", "results"}
    for item in data["results"]:
        assert set(item.keys()) == {
            "internalProductId",
            "retailerProductId",
            "supermarket",
            "supermarketDescription",
            "name",
            "canonicalName",
            "brand",
            "size",
            "category",
            "subcategory",
            "tags",
            "price",
            "unitDescription",
            "unitValue",
            "promoPrice",
            "image",
            "availability",
            "lastUpdated",
            "score",
            "matchType",
            "matchedTerms",
        }


def _assert_autocomplete_contract(payload) -> None:
    data = payload.model_dump(mode="json")
    assert set(data.keys()) == {"query", "total", "suggestions"}
    for item in data["suggestions"]:
        assert set(item.keys()) == {
            "suggestion",
            "displayName",
            "brand",
            "size",
            "category",
            "score",
            "matchType",
        }


def _assert_search_has_expected_signal(
    query: str,
    expected_terms: list[str],
    expected_category: str,
    expected_brands: list[str] | None = None,
) -> None:
    payload = search(q=query, limit=10)
    _assert_search_contract(payload)
    assert payload.total > 0
    assert payload.results[0].category == expected_category, f"query={query!r} top={payload.results[0]}"
    names = [item.name.lower() for item in payload.results[:5]]
    joined = " ".join(names)
    assert any(term in joined for term in expected_terms), f"query={query!r} top_names={names!r}"
    if expected_brands:
        top_brands = [item.brand.lower() for item in payload.results[:5]]
        assert any(brand in top_brands for brand in expected_brands), f"query={query!r} top_brands={top_brands!r}"


def _assert_autocomplete_has_expected_signal(
    query: str,
    expected_terms: list[str],
    expected_category: str,
    expected_brands: list[str] | None = None,
) -> None:
    payload = autocomplete(q=query, limit=5)
    _assert_autocomplete_contract(payload)
    assert payload.total > 0
    suggestions = [item.suggestion.lower() for item in payload.suggestions]
    joined = " ".join(suggestions)
    assert any(term in joined for term in expected_terms), f"query={query!r} suggestions={suggestions!r}"
    assert payload.suggestions[0].category == expected_category, f"query={query!r} top={payload.suggestions[0]}"
    assert len(suggestions) == len(set(suggestions)), f"query={query!r} duplicate suggestions={suggestions!r}"
    if expected_brands:
        top_brands = [item.brand.lower() for item in payload.suggestions[:5]]
        assert any(brand in top_brands for brand in expected_brands), f"query={query!r} top_brands={top_brands!r}"


def test_golden_queries_search_relevance() -> None:
    checks = [
        ("semi skimmed milk", ["semi skimmed", "milk"], "milk", None),
        ("oatly milk", ["oatly", "milk"], "milk", ["oatly"]),
        ("heinz baked beans", ["heinz", "beans"], "bakedBeans", ["heinz"]),
        ("cheddar 400g", ["cheddar", "400g", "400 g"], "cheese", None),
        ("warburtons bread", ["warburtons", "bread"], "bread", ["warburtons"]),
        ("eggs large free range", ["egg", "free range"], "eggs", None),
    ]
    for query, expected_terms, expected_category, expected_brands in checks:
        _assert_search_has_expected_signal(query, expected_terms, expected_category, expected_brands)


def test_golden_queries_autocomplete_relevance() -> None:
    checks = [
        ("semi skimmed milk", ["milk", "semi skimmed"], "milk", None),
        ("oatly milk", ["oatly", "milk"], "milk", ["oatly"]),
        ("heinz baked beans", ["beans", "heinz"], "bakedBeans", ["heinz"]),
        ("cheddar 400g", ["cheddar"], "cheese", None),
        ("warburtons bread", ["bread", "warburtons"], "bread", ["warburtons"]),
        ("eggs large free range", ["egg", "free range"], "eggs", None),
    ]
    for query, expected_terms, expected_category, expected_brands in checks:
        _assert_autocomplete_has_expected_signal(query, expected_terms, expected_category, expected_brands)
