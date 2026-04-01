from __future__ import annotations

import logging
from decimal import Decimal
from typing import Iterable
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

SYNONYM_MAP: dict[str, list[str]] = {
    "beanz": ["beans", "baked beans"],
    "yoghurt": ["yogurt"],
    "fillets": ["fillet", "breast"],
    "loaf": ["bread"],
}


def _normalize_token(token: str) -> str:
    base = "".join(ch for ch in token.lower().strip() if ch.isalnum())
    if len(base) > 3 and base.endswith("ies"):
        return base[:-3] + "y"
    if len(base) > 3 and base.endswith("es"):
        return base[:-2]
    if len(base) > 2 and base.endswith("s"):
        return base[:-1]
    return base


def _expand_tokens(text: str) -> set[str]:
    tokens = {_normalize_token(token) for token in text.lower().split() if token.strip()}
    expanded = set(tokens)
    for token in list(tokens):
        expanded.update(SYNONYM_MAP.get(token, []))
    return {_normalize_token(token) for token in expanded if token}


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
    normalized = _expand_tokens(name)
    rules = [
        (GroceryCategory.milk, {"milk"}),
        (GroceryCategory.bread, {"bread", "loaf"}),
        (GroceryCategory.eggs, {"egg"}),
        (GroceryCategory.butter, {"butter", "spread"}),
        (GroceryCategory.pasta, {"pasta", "penne", "spaghetti", "fusilli"}),
        (GroceryCategory.bakedBeans, {"bean", "beanz"}),
        (GroceryCategory.bananas, {"banana"}),
        (GroceryCategory.chickenBreast, {"chicken", "breast", "fillet"}),
        (GroceryCategory.cereal, {"cereal", "flakes", "granola", "muesli"}),
        (GroceryCategory.cheese, {"cheese", "cheddar", "mozzarella"}),
        (GroceryCategory.tomatoes, {"tomato"}),
        (GroceryCategory.rice, {"rice", "basmati"}),
        (GroceryCategory.yogurt, {"yogurt", "yoghurt"}),
        (GroceryCategory.apples, {"apple"}),
    ]
    for category, keywords in rules:
        if normalized.intersection(keywords):
            return category
    return GroceryCategory.unknown


def _intent_from_item(item_name: str, quantity: int):
    category = _categorize(item_name)
    keywords = COMMON_KEYWORD_MAP.get(category, [item_name.lower()])
    expanded = sorted({_normalize_token(kw) for kw in keywords}.union(_expand_tokens(item_name)))
    return build_intent(item_name, quantity, category, expanded)


def _score_overlap(intent_tokens: set[str], product: SupermarketProduct) -> tuple[int, list[str]]:
    searchable = " ".join([product.name, product.subcategory, product.category.value, *product.tags]).lower()
    product_tokens = _expand_tokens(searchable)
    hits = sorted(intent_tokens.intersection(product_tokens))
    return len(hits), hits


def _rank_candidate(intent, product: SupermarketProduct):
    reasons: list[str] = []
    intent_tokens = set(intent.acceptedKeywords)

    if intent.category != GroceryCategory.unknown and product.category != intent.category:
        return None

    quality = MatchQuality.exact if product.category == intent.category else MatchQuality.acceptableEquivalent
    confidence = Decimal("0.25")

    token_score, hits = _score_overlap(intent_tokens, product)
    if token_score:
        confidence += Decimal(min(token_score, 5)) * Decimal("0.11")
        reasons.append(f"Matched tokens ({token_score}): {', '.join(hits[:5])}.")
    else:
        reasons.append("No token overlap across name/tags/category/subcategory.")

    if intent.normalizedInput in product.name.lower():
        confidence += Decimal("0.25")
        reasons.append("Direct phrase match in product name.")

    if product.isOwnBrand:
        confidence += Decimal("0.03")
        reasons.append("Own-brand value signal applied.")

    if intent.category == GroceryCategory.unknown and token_score < 2 and intent.normalizedInput not in product.name.lower():
        reasons.append("Rejected: weak unknown-category match.")
        return None

    if token_score <= 1 and intent.category == GroceryCategory.unknown:
        quality = MatchQuality.weakSubstitute

    confidence = max(Decimal("0.05"), min(Decimal("0.99"), confidence))
    reasons.append(f"Unit comparison basis: {product.unitDescription} {product.unitValue}.")
    return quality, confidence, reasons


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
    return f"Missing {len(unavailable_items)} item(s): {item_names}. Try broader names, category hints, or add more supermarkets."


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
        debug_top = [f"{candidate[2].name}({candidate[1]})" for candidate in ranked[:3]]
        logger.info(
            "match supermarket=%s item=%s product=%s quality=%s confidence=%s candidates=%s",
            supermarket.name,
            intent.userInput,
            product.name,
            quality.name,
            confidence,
            " | ".join(debug_top),
        )

    return SupermarketBasketTotal(
        id=uuid4(),
        supermarket=supermarket,
        selections=selections,
        unavailableItems=unavailable,
        missingItemsExplanation=_missing_explanation(unavailable),
        total=sum((item.totalPrice for item in selections), Decimal("0.00")),
    )


def _best_options_per_intent(intents, totals: Iterable[SupermarketBasketTotal]):
    for intent in intents:
        options = [selection for total in totals for selection in total.selections if selection.intent.id == intent.id]
        best = min(options, key=lambda option: (option.totalPrice, -option.matchQuality.value, -option.confidence)) if options else None
        yield intent, best


def _build_mixed_basket(intents, totals: list[SupermarketBasketTotal], max_supermarkets: int | None = None) -> MixedBasketResult:
    selections: list[ItemSelectionResult] = []

    if max_supermarkets and max_supermarkets > 0:
        allowed: set[str] = set()
        for intent, best in _best_options_per_intent(intents, totals):
            if not best:
                continue
            if best.supermarket.name in allowed or len(allowed) < max_supermarkets:
                allowed.add(best.supermarket.name)
                selections.append(best)
                continue
            constrained = [
                selection
                for total in totals
                for selection in total.selections
                if selection.intent.id == intent.id and selection.supermarket.name in allowed
            ]
            if constrained:
                selections.append(min(constrained, key=lambda option: (option.totalPrice, -option.matchQuality.value, -option.confidence)))
    else:
        for _, best in _best_options_per_intent(intents, totals):
            if best:
                selections.append(best)

    unavailable = [intent for intent in intents if not any(selection.intent.id == intent.id for selection in selections)]
    return MixedBasketResult(
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

    max_supermarkets = request.maxSupermarkets if getattr(request, "maxSupermarkets", None) else None
    mixed = _build_mixed_basket(intents, totals, max_supermarkets=max_supermarkets)

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
