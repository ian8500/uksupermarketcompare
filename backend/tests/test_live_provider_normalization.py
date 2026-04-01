from decimal import Decimal

from app.services.providers.base import ProviderProduct
from app.services.providers.retailers import TescoProvider


def test_tesco_provider_normalizes_structured_rows(monkeypatch):
    provider = TescoProvider()

    def _fake_load():
        return [
            ProviderProduct(
                source_product_id="abc123",
                name="Tesco British Semi Skimmed Milk",
                subcategory="Milk",
                price=Decimal("1.55"),
                size="2L",
                brand="Tesco",
                unit_description="per litre",
                unit_value=Decimal("0.775"),
                tags=["dairy", "milk"],
                source_metadata={"upstream": "third_party"},
            )
        ]

    monkeypatch.setattr(provider, "load_products", _fake_load)
    normalized = provider.normalize_products()

    assert normalized[0].retailer_name == "Tesco"
    assert normalized[0].raw.source_product_id == "abc123"
    assert normalized[0].normalized_name
    assert normalized[0].normalized_size.normalized_unit in {"l", "ml"}
    assert normalized[0].searchable_text
