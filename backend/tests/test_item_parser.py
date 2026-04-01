from app.services.item_parser import parse_item_input


def test_parser_supports_quantity_prefix_with_x_suffix():
    parsed = parse_item_input("2x milk")
    assert parsed.quantity == 2
    assert parsed.name == "milk"


def test_parser_supports_quantity_prefix_with_space():
    parsed = parse_item_input("4 eggs")
    assert parsed.quantity == 4
    assert parsed.name == "eggs"


def test_parser_falls_back_when_no_prefix():
    parsed = parse_item_input("brown bread", fallback_quantity=3)
    assert parsed.quantity == 3
    assert parsed.name == "brown bread"


def test_parser_extracts_brand_size_and_preferences():
    parsed = parse_item_input("2 heinz organic baked beanz 415g")
    assert parsed.quantity == 2
    assert parsed.brand == "heinz"
    assert parsed.requestedSizeUnit == "g"
    assert parsed.requestedSizeValue == 415
    assert "organic" in parsed.preferenceTags
    assert parsed.corrections
