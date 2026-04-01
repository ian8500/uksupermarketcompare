from app.models import GroceryCategory
from app.services.normalization import (
    build_searchable_text,
    infer_category,
    normalize_brand,
    normalize_product_name,
    normalize_size,
)


def test_unit_normalization_kg_to_g():
    normalized = normalize_size("1.5kg")
    assert normalized.normalized_unit == "g"
    assert normalized.normalized_value == 1500


def test_simple_brand_normalization():
    assert normalize_brand("Kelloggs") == "kellogg's"


def test_category_intent_assignment():
    assert infer_category("Tesco British Semi Skimmed Milk") == GroceryCategory.milk
    assert infer_category("Heinz Baked Beanz") == GroceryCategory.bakedBeans


def test_synonym_handling_in_name_and_searchable_text():
    normalized_name = normalize_product_name("Heinz Baked Beanz")
    assert "baked beans" in normalized_name

    searchable = build_searchable_text("Natural Yoghurt", "Tesco", "500g", ["dairy"])
    assert "yogurt" in searchable
