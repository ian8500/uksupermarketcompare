from app.routes.catalog import CATALOG


def test_catalog_has_required_swift_categories_for_key_supermarkets():
    required = {"dairy", "bakery", "pantry", "fruitVeg", "meat"}
    markets = {market.name: market for market in CATALOG.supermarkets}

    for name in ["Tesco", "ASDA", "Sainsbury's"]:
        assert name in markets
        categories = {product.category for product in markets[name].products}
        assert required.issubset(categories)
