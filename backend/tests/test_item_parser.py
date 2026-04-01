import pytest

from app.services.item_parser import parse_item_input


@pytest.mark.parametrize(
    "raw,quantity,intent,brand,size_unit,size_value,preferences",
    [
        ("milk", 1, "milk", None, None, None, []),
        ("2 milk", 2, "milk", None, None, None, []),
        ("2x milk", 2, "milk", None, None, None, []),
        ("semi skimmed milk", 1, "milk", None, None, None, ["semi skimmed"]),
        ("heinz baked beans", 1, "baked beans", "heinz", None, None, []),
        ("cheddar 400g", 1, "cheddar", None, "g", 400, []),
        ("organic bananas", 1, "bananas", None, None, None, ["organic"]),
        ("cheap pasta", 1, "pasta", None, None, None, ["cheap"]),
        ("own brand eggs", 1, "eggs", None, None, None, ["own", "own brand"]),
        ("toms", 1, "tomatoes", None, None, None, []),
        ("spag", 1, "pasta", None, None, None, []),
        ("yoghurt", 1, "yogurt", None, None, None, []),
        ("3 yogurt", 3, "yogurt", None, None, None, []),
        ("asda milk 2l", 1, "milk", "asda", "l", 2, []),
        ("tesco organic yogurt 500g", 1, "yogurt", "tesco", "g", 500, ["organic"]),
        ("barilla spag 500g", 1, "pasta", "barilla", "g", 500, []),
        ("sainsbury's baked beanz", 1, "baked beans", "sainsbury's", None, None, []),
        ("free-range eggs", 1, "eggs", None, None, None, ["free range"]),
        ("branded only cereal", 1, "cereal", None, None, None, ["branded", "branded only"]),
        ("whole milk", 1, "milk", None, None, None, ["whole"]),
        ("4 heinz beans 415g", 4, "baked beans", "heinz", "g", 415, []),
    ],
)
def test_parser_real_grocery_inputs(raw, quantity, intent, brand, size_unit, size_value, preferences):
    parsed = parse_item_input(raw)

    assert parsed.rawText == raw
    assert parsed.quantity == quantity
    assert parsed.intent == intent
    assert parsed.brand == brand
    assert parsed.requestedSizeUnit == size_unit
    assert parsed.requestedSizeValue == size_value
    assert parsed.preferences == preferences


def test_parser_falls_back_when_no_quantity_prefix():
    parsed = parse_item_input("brown bread", fallback_quantity=3)
    assert parsed.quantity == 3
    assert parsed.intent == "brown bread"
