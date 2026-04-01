from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class GroceryCategory(str, Enum):
    milk = "milk"
    bread = "bread"
    eggs = "eggs"
    butter = "butter"
    pasta = "pasta"
    bakedBeans = "bakedBeans"
    bananas = "bananas"
    chickenBreast = "chickenBreast"
    cereal = "cereal"
    cheese = "cheese"
    tomatoes = "tomatoes"
    rice = "rice"
    yogurt = "yogurt"
    apples = "apples"
    unknown = "unknown"


class MatchQuality(int, Enum):
    exact = 3
    acceptableEquivalent = 2
    weakSubstitute = 1


class BasketComparisonMode(str, Enum):
    cheapestPossible = "cheapestPossible"
    cheapestSingleStoreOnly = "cheapestSingleStoreOnly"


class BrandPreference(str, Enum):
    neutral = "neutral"
    ownBrandPreferred = "ownBrandPreferred"
    brandedPreferred = "brandedPreferred"


class ShoppingItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    quantity: int


class ShoppingList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    title: str
    createdAt: float | str
    items: List[ShoppingItem]


class Supermarket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    description: str


class BasketUserPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brandPreference: BrandPreference
    avoidPremium: bool
    organicOnly: bool


class GroceryIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    userInput: str
    normalizedInput: str
    category: GroceryCategory
    quantity: int
    acceptedKeywords: List[str]


class SupermarketProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    supermarketName: str
    name: str
    category: GroceryCategory
    subcategory: str
    price: Decimal
    size: str
    brand: str
    isOwnBrand: bool
    isPremium: bool
    isOrganic: bool
    unitDescription: str
    unitValue: Decimal
    tags: List[str]


class ItemSelectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    intent: GroceryIntent
    supermarket: Supermarket
    product: SupermarketProduct
    quantity: int
    unitPrice: Decimal
    unitPriceDescription: str
    totalPrice: Decimal
    matchQuality: MatchQuality
    confidence: Decimal
    reasons: List[str]


class SupermarketBasketTotal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    supermarket: Supermarket
    selections: List[ItemSelectionResult]
    unavailableItems: List[GroceryIntent]
    total: Decimal
    missingItemsExplanation: str = "All requested items were matched."


class MixedBasketResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selections: List[ItemSelectionResult]
    unavailableItems: List[GroceryIntent]
    total: Decimal
    missingItemsExplanation: str = "All requested items were matched."


class BasketOptimisationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shoppingList: ShoppingList
    intents: List[GroceryIntent]
    supermarketTotals: List[SupermarketBasketTotal]
    cheapestSingleStore: Optional[SupermarketBasketTotal]
    mixedBasket: MixedBasketResult
    selectedBasket: MixedBasketResult
    comparisonMode: BasketComparisonMode
    preferences: BasketUserPreferences


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shoppingList: ShoppingList
    supermarkets: List[Supermarket]
    comparisonMode: BasketComparisonMode
    preferences: BasketUserPreferences


class CompareResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: BasketOptimisationResult
    savingsVsMostExpensive: Decimal = Field(default=Decimal("0.00"))
    savingsVsCheapestSingleStore: Decimal = Field(default=Decimal("0.00"))


def build_intent(item_name: str, quantity: int, category: GroceryCategory, keywords: list[str]) -> GroceryIntent:
    cleaned = item_name.strip()
    return GroceryIntent(
        id=uuid4(),
        userInput=cleaned,
        normalizedInput=cleaned.lower(),
        category=category,
        quantity=max(1, quantity),
        acceptedKeywords=keywords,
    )
