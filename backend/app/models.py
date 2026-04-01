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
    bestConvenienceOption = "bestConvenienceOption"


class BasketDecisionMode(str, Enum):
    cheapestSingleStore = "cheapestSingleStore"
    cheapestMixedBasket = "cheapestMixedBasket"
    bestConvenienceOption = "bestConvenienceOption"
    cheapestMixedBasketMaxTwoStores = "cheapestMixedBasketMaxTwoStores"


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
    score: Decimal
    matchedTokens: List[str] = []
    reasons: List[str]
    tradeoffs: List[str] = []


class MissingItemCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supermarketName: str
    productName: str
    score: Decimal
    reason: str


class MissingItemDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: GroceryIntent
    reason: str
    closeCandidates: List[MissingItemCandidate] = []
    suggestion: str


class SupermarketBasketTotal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    supermarket: Supermarket
    selections: List[ItemSelectionResult]
    unavailableItems: List[GroceryIntent]
    total: Decimal
    missingItemsExplanation: str = "All requested items were matched."
    missingItemDetails: List[MissingItemDetail] = []


class MixedBasketResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selections: List[ItemSelectionResult]
    unavailableItems: List[GroceryIntent]
    total: Decimal
    storesUsed: int = 0
    missingItemsExplanation: str = "All requested items were matched."
    missingItemDetails: List[MissingItemDetail] = []


class StoreAllocationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    storeName: str
    itemCount: int
    totalSpend: Decimal


class SavingsSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    versusCheapestMixedBasket: Decimal = Field(default=Decimal("0.00"))
    versusCheapestSingleStore: Decimal = Field(default=Decimal("0.00"))
    versusMostExpensiveSingleStore: Decimal = Field(default=Decimal("0.00"))
    explanation: str = ""


class MissingItemsSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = 0
    itemNames: List[str] = []
    explanation: str = "All requested items were matched."


class PurchasePlanItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    originalUserItem: GroceryIntent
    selectedProduct: SupermarketProduct | None = None
    selectedStore: Supermarket | None = None
    quantity: int
    price: Decimal
    explanation: str
    matchConfidence: Decimal | None = None


class PurchasePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: BasketDecisionMode
    basket: MixedBasketResult
    items: List[PurchasePlanItem] = []
    allocation: List[StoreAllocationSummary]
    savings: SavingsSummary = SavingsSummary()
    missingItems: MissingItemsSummary = MissingItemsSummary()
    unavailableItemsCount: int


class BasketStrategyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: BasketDecisionMode
    plan: PurchasePlan
    totalPrice: Decimal = Field(default=Decimal("0.00"))
    storesUsed: List[str] = []
    storeCount: int = 0
    savings: SavingsSummary = SavingsSummary()
    missingItemsCount: int = 0
    chosenItems: List[PurchasePlanItem] = []
    explanation: str = ""
    tradeoffSummary: str = ""
    wonBecause: str
    tradeoffs: List[str] = []
    score: Decimal


class BasketSummaryCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    total: Decimal
    subtitle: str


class SavingsExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amountVsMostExpensive: Decimal
    amountVsCheapestSingleStore: Decimal
    explanation: str


class BasketOptimisationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shoppingList: ShoppingList
    intents: List[GroceryIntent]
    supermarketTotals: List[SupermarketBasketTotal]
    cheapestSingleStore: Optional[SupermarketBasketTotal]
    mixedBasket: MixedBasketResult
    bestConvenienceBasket: MixedBasketResult
    selectedBasket: MixedBasketResult
    comparisonMode: BasketComparisonMode
    preferences: BasketUserPreferences
    maxSupermarkets: int | None = None
    summaryCards: List[BasketSummaryCard] = []
    strategyResults: List[BasketStrategyResult] = []
    selectedStrategyMode: BasketDecisionMode | None = None


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shoppingList: ShoppingList
    supermarkets: List[Supermarket]
    comparisonMode: BasketComparisonMode
    preferences: BasketUserPreferences
    maxSupermarkets: int | None = None


class CompareResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: BasketOptimisationResult
    savingsVsMostExpensive: Decimal = Field(default=Decimal("0.00"))
    savingsVsCheapestSingleStore: Decimal = Field(default=Decimal("0.00"))
    savingsExplanation: SavingsExplanation


class SavedBasketRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    shoppingList: ShoppingList
    lastResult: Optional[BasketOptimisationResult] = None


class SavedBasketUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shoppingList: ShoppingList


class SavedBasketRerunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supermarkets: List[Supermarket]
    comparisonMode: BasketComparisonMode
    preferences: BasketUserPreferences
    maxSupermarkets: int | None = None


class ParsedItemSize(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Decimal
    unit: str


class ParsedItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rawText: str
    quantity: int
    intent: str
    brand: str | None = None
    size: ParsedItemSize | None = None
    preferences: List[str] = []

    @property
    def name(self) -> str:
        return self.intent

    @property
    def requestedSizeValue(self) -> Decimal | None:
        return self.size.value if self.size else None

    @property
    def requestedSizeUnit(self) -> str | None:
        return self.size.unit if self.size else None

    @property
    def preferenceTags(self) -> List[str]:
        return self.preferences


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
