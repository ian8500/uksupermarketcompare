from uuid import uuid4

import pytest

from app.models import BasketComparisonMode, BasketUserPreferences, BrandPreference, CompareRequest, ShoppingItem, ShoppingList, Supermarket
from app.services.mock_compare_service import build_comparison


REALISTIC_INPUTS = [
    "milk", "semi skimmed milk", "2 milk", "whole milk", "organic milk", "bread", "wholemeal bread", "white loaf",
    "eggs", "free range eggs", "dozen eggs", "butter", "salted butter", "pasta", "penne pasta", "spaghetti",
    "heinz baked beans", "baked beanz", "bananas", "organic bananas", "chicken breast", "chicken breast fillets",
    "corn flakes", "kellogg cereal", "cheddar", "cheddar 400g", "tomatoes", "cherry tomatoes", "rice", "basmati rice",
    "yoghurt", "greek yogurt", "apples", "gala apples", "tesco milk", "asda baked beans", "sainsbury bread", "lurpak butter",
    "cathedral city cheddar", "tilda rice",
]


def _request(item_name: str) -> CompareRequest:
    return CompareRequest(
        shoppingList=ShoppingList(
            id=uuid4(),
            title="realistic",
            createdAt="2026-04-01T00:00:00Z",
            items=[ShoppingItem(id=uuid4(), name=item_name, quantity=1)],
        ),
        supermarkets=[
            Supermarket(id=uuid4(), name="Tesco", description=""),
            Supermarket(id=uuid4(), name="ASDA", description=""),
            Supermarket(id=uuid4(), name="Sainsbury's", description=""),
        ],
        comparisonMode=BasketComparisonMode.cheapestPossible,
        preferences=BasketUserPreferences(brandPreference=BrandPreference.neutral, avoidPremium=False, organicOnly=False),
    )


@pytest.mark.parametrize("item_name", REALISTIC_INPUTS)
def test_phase1_realistic_inputs_are_matchable_or_explained(item_name: str):
    response = build_comparison(_request(item_name))

    assert len(response.result.intents) == 1
    if response.result.selectedBasket.unavailableItems:
        assert response.result.selectedBasket.missingItemDetails
        assert response.result.selectedBasket.missingItemDetails[0].suggestion
    else:
        selection = response.result.selectedBasket.selections[0]
        assert selection.score >= 0.30
        assert selection.reasons
