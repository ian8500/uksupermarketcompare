from uuid import uuid4

from app.models import (
    BasketComparisonMode,
    BasketUserPreferences,
    BrandPreference,
    CompareRequest,
    SavedBasketRerunRequest,
    SavedBasketUpsertRequest,
    ShoppingItem,
    ShoppingList,
    Supermarket,
)
from app.routes.saved_baskets import create_saved_basket, duplicate_saved_basket, edit_saved_basket, rerun_saved_basket
from app.services.mock_compare_service import build_comparison


def _shopping_list() -> ShoppingList:
    return ShoppingList(
        id=uuid4(),
        title="Weekly",
        createdAt="2026-04-01T00:00:00Z",
        items=[
            ShoppingItem(id=uuid4(), name="2x milk", quantity=1),
            ShoppingItem(id=uuid4(), name="bread", quantity=1),
        ],
    )


def _markets() -> list[Supermarket]:
    return [
        Supermarket(id=uuid4(), name="Tesco", description=""),
        Supermarket(id=uuid4(), name="ASDA", description=""),
    ]


def _prefs() -> BasketUserPreferences:
    return BasketUserPreferences(brandPreference=BrandPreference.neutral, avoidPremium=False, organicOnly=False)


def test_compare_contract_contains_summary_and_explanations():
    response = build_comparison(
        CompareRequest(
            shoppingList=_shopping_list(),
            supermarkets=_markets(),
            comparisonMode=BasketComparisonMode.cheapestPossible,
            preferences=_prefs(),
            maxSupermarkets=2,
        )
    )

    assert response.savingsExplanation.explanation
    assert len(response.result.summaryCards) == 3
    assert response.result.bestConvenienceBasket.total >= 0


def test_saved_basket_create_duplicate_edit_and_rerun_flow():
    created = create_saved_basket(
        SavedBasketUpsertRequest(
            shoppingList=_shopping_list(),
            tags=["weekly", "family"],
            notes="Baseline weekly basket",
        )
    )
    assert created.tags == ["weekly", "family"]
    assert created.notes == "Baseline weekly basket"
    assert created.rerunCount == 0
    assert created.lastRerunAt is None

    duplicate = duplicate_saved_basket(str(created.id))
    assert duplicate.shoppingList.title.endswith("(Copy)")
    assert duplicate.tags == ["weekly", "family"]
    assert duplicate.notes == "Baseline weekly basket"

    edited_list = _shopping_list().model_copy(update={"id": created.shoppingList.id, "title": "Weekly Edited"})
    edited = edit_saved_basket(
        str(created.id),
        SavedBasketUpsertRequest(shoppingList=edited_list, tags=["edited"], notes="Updated list"),
    )
    assert edited.shoppingList.title == "Weekly Edited"
    assert edited.tags == ["edited"]
    assert edited.notes == "Updated list"

    rerun = rerun_saved_basket(
        str(created.id),
        SavedBasketRerunRequest(
            supermarkets=_markets(),
            comparisonMode=BasketComparisonMode.cheapestPossible,
            preferences=_prefs(),
            maxSupermarkets=1,
        ),
    )
    assert rerun.lastResult is not None
    assert rerun.rerunCount == 1
    assert rerun.lastRerunAt is not None
