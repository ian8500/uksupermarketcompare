from basketcompare.comparison import BasketComparisonService
from basketcompare.fixtures import SeededProviderRegistry
from basketcompare.matching import ConfidenceScorer
from basketcompare.models import ConfidenceBand, RawProduct, Unit
from basketcompare.normalization import CanonicalProductNormalizer
from basketcompare.ui import render_results
from basketcompare.admin import build_debug_screen


def _service() -> BasketComparisonService:
    registry = SeededProviderRegistry()
    return BasketComparisonService(providers=registry.providers)


def test_pack_size_parsing_realistic_cases_30():
    normalizer = CanonicalProductNormalizer()
    cases = [
        ("Milk 2L", 2000, Unit.ML),
        ("Water 1.5L", 1500, Unit.ML),
        ("Pasta 500g", 500, Unit.G),
        ("Rice 1kg", 1000, Unit.G),
        ("Juice 750ml", 750, Unit.ML),
        ("Beans 4 x 415g", 1660, Unit.G),
        ("Yogurt 6x125g", 750, Unit.G),
        ("Eggs 12 pack", 12, Unit.COUNT),
        ("Bagels 5 count", 5, Unit.COUNT),
        ("Pepsi 8 x 330ml", 2640, Unit.ML),
        ("Flour 2kg", 2000, Unit.G),
        ("Butter 250 g", 250, Unit.G),
        ("Soup 600 ml", 600, Unit.ML),
        ("Oil 1 l", 1000, Unit.ML),
        ("Nuggets 20ct", 20, Unit.COUNT),
        ("Tea 80 count", 80, Unit.COUNT),
        ("Chocolate 3x100g", 300, Unit.G),
        ("Cola 24x330ml", 7920, Unit.ML),
        ("Cheese 400g", 400, Unit.G),
        ("Ham 150g", 150, Unit.G),
        ("Tomatoes 4 pack", 4, Unit.COUNT),
        ("Porridge 1 kg", 1000, Unit.G),
        ("Lemonade 2 x 1.5l", 3000, Unit.ML),
        ("Baby wipes 64ct", 64, Unit.COUNT),
        ("Tuna 4x145g", 580, Unit.G),
        ("Coffee 200g", 200, Unit.G),
        ("Sparkling water 500ml", 500, Unit.ML),
        ("Orange squash 1.5 l", 1500, Unit.ML),
        ("Crisps 6x25g", 150, Unit.G),
        ("Muffins 4 pk", 4, Unit.COUNT),
    ]

    for text, expected_amount, expected_unit in cases:
        parsed = normalizer.parse_pack_size(text)
        assert parsed is not None, text
        assert round(parsed.normalized_amount, 2) == expected_amount, text
        assert parsed.normalized_unit == expected_unit, text


def test_confidence_bands_exact_close_substitute():
    n = CanonicalProductNormalizer()
    scorer = ConfidenceScorer()

    wanted = n.normalize(RawProduct("query", "Q", "Heinz Baked Beans 4x415g", "Heinz", 0, "tinned"))
    exact = n.normalize(RawProduct("tesco", "1", "Heinz Baked Beans 4 x 415g", "Heinz", 3.75, "tinned"))
    close = n.normalize(RawProduct("asda", "2", "Heinz Baked Beans 415g", "Heinz", 1.05, "tinned"))
    sub = n.normalize(RawProduct("s", "3", "Branston Baked Beans 4x410g", "Branston", 2.95, "tinned"))

    _, exact_band, _ = scorer.score(wanted, exact)
    _, close_band, _ = scorer.score(wanted, close)
    _, sub_band, _ = scorer.score(wanted, sub)

    assert exact_band == ConfidenceBand.EXACT
    assert close_band in {ConfidenceBand.CLOSE, ConfidenceBand.EXACT}
    assert sub_band in {ConfidenceBand.SUBSTITUTE, ConfidenceBand.CLOSE}


def test_basket_algorithms_and_ui_and_debug():
    service = _service()
    queries = [
        "Semi skimmed milk 2L",
        "Baked beans 4x415g",
        "Free range eggs 12 pack",
        "Fusilli pasta 500g",
        "Mature cheddar 350g",
        "Apple juice 1L",
    ]

    result = service.compare(queries, allow_substitutions=True)
    assert "cheapest_basket_overall" in result
    assert "cheapest_single_store_basket" in result
    assert "cheapest_with_own_brand_substitutions" in result

    overall = result["cheapest_basket_overall"]
    ui = render_results(overall)
    assert ui["items"]
    assert all("why_matched" in i for i in ui["items"])

    debug_rows = build_debug_screen(service)
    assert len(debug_rows) >= 18
    assert {"raw_title", "canonical_name", "tokens"}.issubset(debug_rows[0].keys())
