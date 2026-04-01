from uuid import uuid4

from app.models import BasketComparisonMode, BasketUserPreferences, BrandPreference, CompareRequest, ShoppingItem, ShoppingList, Supermarket
from app.services.mock_compare_service import build_comparison



def _request(*items: tuple[str, int], max_supermarkets: int | None = None) -> CompareRequest:
    return CompareRequest(
        shoppingList=ShoppingList(
            id=uuid4(),
            title="reliability",
            createdAt="2026-04-01T00:00:00Z",
            items=[ShoppingItem(id=uuid4(), name=name, quantity=qty) for name, qty in items],
        ),
        supermarkets=[
            Supermarket(id=uuid4(), name="Tesco", description=""),
            Supermarket(id=uuid4(), name="ASDA", description=""),
            Supermarket(id=uuid4(), name="Sainsbury's", description=""),
        ],
        comparisonMode=BasketComparisonMode.cheapestPossible,
        preferences=BasketUserPreferences(brandPreference=BrandPreference.neutral, avoidPremium=False, organicOnly=False),
        maxSupermarkets=max_supermarkets,
    )


def test_common_seed_items_are_matchable_across_all_supermarkets():
    response = build_comparison(_request(("milk", 1), ("bread", 1), ("eggs", 1), ("butter", 1)))

    assert response.result.supermarketTotals
    for total in response.result.supermarketTotals:
        assert total.unavailableItems == []
        assert len(total.selections) == 4
        assert total.missingItemsExplanation == "All requested items were matched."


def test_quantity_scales_selection_totals():
    response = build_comparison(_request(("2x milk", 1)))
    selected = response.result.selectedBasket.selections[0]

    assert selected.quantity == 2
    assert selected.totalPrice == selected.unitPrice * 2


def test_fuzzy_and_synonym_matching_for_generic_terms():
    response = build_comparison(_request(("milks", 1), ("baked beanz", 1), ("yoghurts", 1)))
    assert response.result.selectedBasket.unavailableItems == []


def test_missing_items_have_clear_explanation():
    response = build_comparison(_request(("dragon fruit soda", 1)))

    assert response.result.selectedBasket.unavailableItems
    assert "Missing 1 item(s): dragon fruit soda" in response.result.selectedBasket.missingItemsExplanation


def test_matching_logs_include_match_and_candidate_reasons(caplog):
    caplog.set_level("INFO")
    build_comparison(_request(("milk", 1), ("unfindable mystery item", 1)))

    logs = "\n".join(message for _, _, message in caplog.record_tuples)
    assert "match supermarket=Tesco item=milk" in logs
    assert "candidates=" in logs
    assert "no-match supermarket=Tesco item=unfindable mystery item" in logs
    assert "analytics event=compare_completed" in logs


def test_mixed_basket_honours_max_supermarket_limit():
    response = build_comparison(_request(("milk", 1), ("bread", 1), ("cheese", 1), max_supermarkets=1))

    stores = {selection.supermarket.name for selection in response.result.mixedBasket.selections}
    assert len(stores) <= 1
