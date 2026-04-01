from uuid import uuid4

from app.models import BasketComparisonMode, BasketUserPreferences, BrandPreference, CompareRequest, ShoppingItem, ShoppingList, Supermarket
from app.services.mock_compare_service import build_comparison


def _request(*item_names: str) -> CompareRequest:
    return CompareRequest(
        shoppingList=ShoppingList(
            id=uuid4(),
            title="reliability",
            createdAt="2026-04-01T00:00:00Z",
            items=[ShoppingItem(id=uuid4(), name=name, quantity=1) for name in item_names],
        ),
        supermarkets=[
            Supermarket(id=uuid4(), name="Tesco", description=""),
            Supermarket(id=uuid4(), name="ASDA", description=""),
            Supermarket(id=uuid4(), name="Sainsbury's", description=""),
        ],
        comparisonMode=BasketComparisonMode.cheapestPossible,
        preferences=BasketUserPreferences(brandPreference=BrandPreference.neutral, avoidPremium=False, organicOnly=False),
    )


def test_common_seed_items_are_matchable_across_all_supermarkets():
    response = build_comparison(_request("milk", "bread", "eggs", "butter"))

    assert response.result.supermarketTotals
    for total in response.result.supermarketTotals:
        assert total.unavailableItems == []
        assert len(total.selections) == 4
        assert total.missingItemsExplanation == "All requested items were matched."


def test_missing_items_have_clear_explanation():
    response = build_comparison(_request("dragon fruit soda"))

    assert response.result.selectedBasket.unavailableItems
    assert "Missing 1 item(s): dragon fruit soda" in response.result.selectedBasket.missingItemsExplanation


def test_matching_logs_include_match_and_no_match_reasons(caplog):
    caplog.set_level("INFO")
    build_comparison(_request("milk", "unfindable mystery item"))

    logs = "\n".join(message for _, _, message in caplog.record_tuples)
    assert "match supermarket=Tesco item=milk" in logs
    assert "no-match supermarket=Tesco item=unfindable mystery item" in logs
