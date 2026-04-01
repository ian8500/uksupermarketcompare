from app.services.providers.live_sources import OpenFoodFactsProvider


def test_open_food_facts_unavailable_graceful(monkeypatch):
    provider = OpenFoodFactsProvider(base_url="http://127.0.0.1:9")
    payload = provider.enrich_barcode("5000112548167")
    assert payload["barcode"] == "5000112548167"
    assert payload["status"] == "unavailable"
    assert payload["source"] == "openfoodfacts"
