from app.routes.catalog import CATALOG


def test_catalog_has_common_items_for_key_supermarkets():
    required = {"milk", "bread", "eggs", "butter"}
    markets = {market.name: market for market in CATALOG.supermarkets}

    for name in ["Tesco", "ASDA", "Sainsbury's"]:
        assert name in markets
        categories = {product.category.value for product in markets[name].products}
        assert required.issubset(categories)
