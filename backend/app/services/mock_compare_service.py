from __future__ import annotations

import logging
from decimal import Decimal
from uuid import uuid4

from app.models import (
    BasketOptimisationResult,
    CompareRequest,
    CompareResponse,
    GroceryCategory,
    ItemSelectionResult,
    MatchQuality,
    MixedBasketResult,
    Supermarket,
    SupermarketBasketTotal,
    SupermarketProduct,
    build_intent,
)
from app.services.seed_catalog import COMMON_KEYWORD_MAP, SEEDED_SUPERMARKETS

logger = logging.getLogger(__name__)


def _seeded_product_map() -> dict[str, list[SupermarketProduct]]:
    mapped: dict[str, list[SupermarketProduct]] = {}
    for market in SEEDED_SUPERMARKETS:
        mapped[market["name"].lower()] = [
            SupermarketProduct(
                id=uuid4(),
                supermarketName=market["name"],
                **product,
            )
            for product in market["products"]
        ]
    return mapped


def _categorize(name: str) -> GroceryCategory:
    normalized = name.strip().lower()
    rules = [
        (GroceryCategory.milk, ["milk"]),
        (GroceryCategory.bread, ["bread", "loaf"]),
        (GroceryCategory.eggs, ["egg", "eggs"]),
        (GroceryCategory.butter, ["butter", "spread"]),
        (GroceryCategory.pasta, ["pasta", "penne", "spaghetti"]),
        (GroceryCategory.bakedBeans, ["beans"]),
        (GroceryCategory.rice, ["rice"]),
        (GroceryCategory.cheese, ["cheese", "cheddar"]),
    ]
    for category, keywords in rules:
        if any(keyword in normalized for keyword in keywords):
            return category
    return GroceryCategory.unknown


def _intent_from_item(item_name: str, quantity: int):
    category = _categorize(item_name)
    keywords = COMMON_KEYWORD_MAP.get(category, [item_name.lower()])
    return build_intent(item_name, quantity, category, keywords)


def _rank_candidate(intent, product: SupermarketProduct):
    reasons: list[str] = []
    if intent.category != GroceryCategory.unknown and product.category != intent.category:
        return None

    quality = MatchQuality.exact if product.category == intent.category else MatchQuality.acceptableEquivalent
    confidence = Decimal("0.45")

    keyword_hits = [kw for kw in intent.acceptedKeywords if kw in product.name.lower() or kw in product.tags]
    if keyword_hits:
        confidence += Decimal(min(len(keyword_hits), 3)) * Decimal("0.12")
        reasons.append(f"Keyword hits: {', '.join(keyword_hits[:3])}.")
    else:
        reasons.append("No keyword hits; category-only match.")

    if product.isOwnBrand:
        confidence += Decimal("0.05")
        reasons.append("Own-brand value signal applied.")

    reasons.append(f"Unit comparison basis: {product.unitDescription} {product.unitValue}.")
    return quality, max(Decimal("0.10"), min(Decimal("0.99"), confidence)), reasons


def _selection(intent, supermarket: Supermarket, product: SupermarketProduct, quality: MatchQuality, confidence: Decimal, reasons: list[str]) -> ItemSelectionResult:
    quantity = intent.quantity
    total = product.price * Decimal(quantity)
    return ItemSelectionResult(
        id=uuid4(),
        intent=intent,
        supermarket=supermarket,
        product=product,
        quantity=quantity,
        unitPrice=product.price,
        unitPriceDescription=f"{product.unitDescription} {product.unitValue}",
        totalPrice=total,
        matchQuality=quality,
        confidence=confidence,
        reasons=reasons,
    )


def _missing_explanation(unavailable_items) -> str:
    if not unavailable_items:
        return "All requested items were matched."
    item_names = ", ".join(intent.userInput for intent in unavailable_items)
    return f"Missing {len(unavailable_items)} item(s): {item_names}. Try broader names or add more supermarkets."


def _build_market_total(supermarket: Supermarket, intents, inventory: list[SupermarketProduct]) -> SupermarketBasketTotal:
    selections: list[ItemSelectionResult] = []
    unavailable = []

    for intent in intents:
        ranked: list[tuple[MatchQuality, Decimal, SupermarketProduct, list[str]]] = []
        for product in inventory:
            scored = _rank_candidate(intent, product)
            if scored is None:
                continue
            quality, confidence, reasons = scored
            ranked.append((quality, confidence, product, reasons))

        ranked.sort(key=lambda item: (-item[0].value, item[2].unitValue, item[2].price, -item[1]))

        if not ranked:
            unavailable.append(intent)
            logger.info("no-match supermarket=%s item=%s category=%s reason=no candidates survived filters", supermarket.name, intent.userInput, intent.category.value)
            continue

        quality, confidence, product, reasons = ranked[0]
        selections.append(_selection(intent, supermarket, product, quality, confidence, reasons))
        logger.info(
            "match supermarket=%s item=%s product=%s quality=%s confidence=%s",
            supermarket.name,
            intent.userInput,
            product.name,
            quality.name,
            confidence,
        )

    return SupermarketBasketTotal(
        id=uuid4(),
        supermarket=supermarket,
        selections=selections,
        unavailableItems=unavailable,
        missingItemsExplanation=_missing_explanation(unavailable),
        total=sum((item.totalPrice for item in selections), Decimal("0.00")),
    )


def build_comparison(request: CompareRequest) -> CompareResponse:
    product_map = _seeded_product_map()

    intents = [_intent_from_item(item.name, item.quantity) for item in request.shoppingList.items]

    totals = []
    for supermarket in request.supermarkets:
        inventory = product_map.get(supermarket.name.lower(), [])
        totals.append(_build_market_total(supermarket, intents, inventory))

    totals = sorted(totals, key=lambda x: x.total)
    cheapest_single = next((total for total in totals if not total.unavailableItems), totals[0] if totals else None)

    mixed_selections: list[ItemSelectionResult] = []
    for intent in intents:
        options = [selection for total in totals for selection in total.selections if selection.intent.id == intent.id]
        if options:
            best = min(options, key=lambda option: (option.totalPrice, -option.matchQuality.value, -option.confidence))
            mixed_selections.append(best)

    mixed_unavailable = [intent for intent in intents if not any(selection.intent.id == intent.id for selection in mixed_selections)]
    mixed = MixedBasketResult(
        selections=mixed_selections,
        unavailableItems=mixed_unavailable,
        missingItemsExplanation=_missing_explanation(mixed_unavailable),
        total=sum((item.totalPrice for item in mixed_selections), Decimal("0.00")),
    )

    selected = mixed if request.comparisonMode.value == "cheapestPossible" else MixedBasketResult(
        selections=cheapest_single.selections if cheapest_single else [],
        unavailableItems=cheapest_single.unavailableItems if cheapest_single else intents,
        missingItemsExplanation=cheapest_single.missingItemsExplanation if cheapest_single else _missing_explanation(intents),
        total=cheapest_single.total if cheapest_single else Decimal("0.00"),
    )

    result = BasketOptimisationResult(
        shoppingList=request.shoppingList,
        intents=intents,
        supermarketTotals=totals,
        cheapestSingleStore=cheapest_single,
        mixedBasket=mixed,
        selectedBasket=selected,
        comparisonMode=request.comparisonMode,
        preferences=request.preferences,
    )

    most_expensive_total = totals[-1].total if totals else Decimal("0.00")
    savings_vs_most_expensive = most_expensive_total - selected.total
    savings_vs_cheapest_single = (cheapest_single.total - selected.total) if cheapest_single else Decimal("0.00")

    return CompareResponse(
        result=result,
        savingsVsMostExpensive=savings_vs_most_expensive,
        savingsVsCheapestSingleStore=savings_vs_cheapest_single,
    )
