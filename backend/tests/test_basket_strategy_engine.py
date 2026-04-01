from uuid import uuid4

from app.models import BasketComparisonMode, BasketUserPreferences, BrandPreference, CompareRequest, ShoppingItem, ShoppingList, Supermarket
from app.services.mock_compare_service import build_comparison


def _request(mode: BasketComparisonMode = BasketComparisonMode.cheapestPossible, max_supermarkets: int | None = None) -> CompareRequest:
    return CompareRequest(
        shoppingList=ShoppingList(
            id=uuid4(),
            title="strategy",
            createdAt="2026-04-01T00:00:00Z",
            items=[
                ShoppingItem(id=uuid4(), name="milk", quantity=1),
                ShoppingItem(id=uuid4(), name="bread", quantity=1),
                ShoppingItem(id=uuid4(), name="eggs", quantity=1),
                ShoppingItem(id=uuid4(), name="cheese", quantity=1),
            ],
        ),
        supermarkets=[
            Supermarket(id=uuid4(), name="Tesco", description=""),
            Supermarket(id=uuid4(), name="ASDA", description=""),
            Supermarket(id=uuid4(), name="Sainsbury's", description=""),
        ],
        comparisonMode=mode,
        preferences=BasketUserPreferences(brandPreference=BrandPreference.neutral, avoidPremium=False, organicOnly=False),
        maxSupermarkets=max_supermarkets,
    )


def test_cheapest_single_store_strategy_returns_complete_best_store():
    response = build_comparison(_request(mode=BasketComparisonMode.cheapestSingleStoreOnly))

    cheapest_single = response.result.cheapestSingleStore
    assert cheapest_single is not None
    assert cheapest_single.unavailableItems == []
    assert response.result.selectedBasket.total == cheapest_single.total
    assert response.result.selectedBasket.storesUsed <= 1


def test_cheapest_mixed_strategy_minimizes_total_and_tracks_store_count():
    response = build_comparison(_request(mode=BasketComparisonMode.cheapestPossible))

    mixed = response.result.mixedBasket
    assert mixed.total <= response.result.cheapestSingleStore.total
    assert mixed.storesUsed >= 1
    assert mixed.storesUsed <= len(response.result.supermarketTotals)


def test_best_convenience_prefers_fewer_stores_while_remaining_price_aware():
    response = build_comparison(_request(mode=BasketComparisonMode.bestConvenienceOption))

    convenience = response.result.bestConvenienceBasket
    mixed = response.result.mixedBasket

    assert response.result.selectedBasket.total == convenience.total
    assert convenience.storesUsed <= max(1, mixed.storesUsed)
    assert any(
        "Costs £" in tradeoff and "cheapest mixed basket" in tradeoff
        for strategy in response.result.strategyResults
        if strategy.mode.value == "bestConvenienceOption"
        for tradeoff in strategy.tradeoffs
    )


def test_strategy_results_include_richer_decision_oriented_fields():
    response = build_comparison(_request(mode=BasketComparisonMode.cheapestPossible))

    strategies = response.result.strategyResults
    assert len(strategies) == 4

    mixed = next(strategy for strategy in strategies if strategy.mode.value == "cheapestMixedBasket")
    assert mixed.totalPrice == mixed.plan.basket.total
    assert mixed.storeCount == len(mixed.storesUsed)
    assert mixed.missingItemsCount == mixed.plan.missingItems.count
    assert mixed.chosenItems == mixed.plan.items
    assert mixed.explanation
    assert mixed.tradeoffSummary
    assert mixed.savings.versusCheapestMixedBasket == 0
    assert mixed.plan.savings.versusCheapestMixedBasket == 0

    first_item = mixed.chosenItems[0]
    assert first_item.originalUserItem.userInput
    assert first_item.quantity >= 1
    assert first_item.explanation
    if first_item.selectedProduct is not None:
        assert first_item.selectedStore is not None
        assert first_item.price > 0
        assert first_item.matchConfidence is not None


def test_strategy_savings_calculation_matches_totals():
    response = build_comparison(_request(mode=BasketComparisonMode.cheapestPossible))
    strategies = {strategy.mode.value: strategy for strategy in response.result.strategyResults}
    mixed = strategies["cheapestMixedBasket"]
    single = strategies["cheapestSingleStore"]

    expected_vs_mixed = mixed.totalPrice - single.totalPrice
    assert single.savings.versusCheapestMixedBasket == expected_vs_mixed
    assert single.plan.savings.versusCheapestMixedBasket == expected_vs_mixed
