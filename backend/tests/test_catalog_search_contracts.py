from app.routes.catalog import catalog
from app.routes.diagnostics import catalog_metrics, search_metrics
from app.routes.search import autocomplete, search

SWIFT_CATEGORIES = {
    "milk",
    "bread",
    "eggs",
    "butter",
    "pasta",
    "bakedBeans",
    "bananas",
    "chickenBreast",
    "cereal",
    "cheese",
    "tomatoes",
    "rice",
    "yogurt",
    "apples",
    "unknown",
}


def test_catalog_contract_remains_swift_compatible() -> None:
    payload = catalog().model_dump(mode="json")

    assert set(payload.keys()) == {"supermarkets", "metadata"}
    assert set(payload["metadata"].keys()) == {"source", "debugMarker", "generatedAt"}

    for market in payload["supermarkets"]:
        assert set(market.keys()) == {"name", "description", "products"}
        for product in market["products"]:
            assert set(product.keys()) == {
                "name",
                "category",
                "subcategory",
                "price",
                "size",
                "brand",
                "isOwnBrand",
                "isPremium",
                "isOrganic",
                "unitDescription",
                "unitValue",
                "tags",
            }
            assert product["category"] in SWIFT_CATEGORIES


def test_search_contract_shape_is_stable() -> None:
    payload = search(q="milk", limit=3).model_dump(mode="json")

    assert set(payload.keys()) == {"query", "normalizedQuery", "total", "results"}
    for item in payload["results"]:
        assert set(item.keys()) == {
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
            "score",
            "matchType",
            "matchedTerms",
        }


def test_autocomplete_contract_shape_is_stable() -> None:
    payload = autocomplete(q="semi", limit=3).model_dump(mode="json")

    assert set(payload.keys()) == {"query", "total", "suggestions"}
    for item in payload["suggestions"]:
        assert set(item.keys()) == {
            "suggestion",
            "displayName",
            "brand",
            "size",
            "category",
            "score",
            "matchType",
        }


def test_diagnostics_endpoints_expose_catalog_and_search_health() -> None:
    search(q="qwertyuiop-no-match", limit=3)
    catalog_payload = catalog_metrics().model_dump(mode="json")
    search_payload = search_metrics().model_dump(mode="json")

    assert set(catalog_payload.keys()) == {
        "productsPerSupermarket",
        "canonicalProducts",
        "mappings",
        "categoriesCovered",
        "priceSnapshots",
        "priceDropAlertCandidates",
    }
    assert catalog_payload["canonicalProducts"] > 0
    assert catalog_payload["mappings"] > 0
    assert catalog_payload["productsPerSupermarket"]

    assert set(search_payload.keys()) == {"totalQueries", "missQueries", "missRate", "weakMatches", "avgTopScore", "byEndpoint"}
    assert search_payload["totalQueries"] >= 1
    assert search_payload["missQueries"] >= 1
