from app.routes.catalog import CATALOG


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


def test_catalog_categories_are_swift_compatible_for_key_supermarkets():
    markets = {market.name: market for market in CATALOG.supermarkets}

    for name in ["Tesco", "ASDA", "Sainsbury's"]:
        assert name in markets
        categories = {product.category for product in markets[name].products}
        assert categories
        assert categories.issubset(SWIFT_CATEGORIES)


def test_catalog_includes_live_debug_marker_metadata():
    assert CATALOG.metadata.debugMarker == "LIVE_CATALOG_V3_MATCHING_INTELLIGENCE"
