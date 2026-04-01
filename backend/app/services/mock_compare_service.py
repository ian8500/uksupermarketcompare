from __future__ import annotations

import logging
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Iterable
from uuid import uuid4

from app.models import (
    BasketOptimisationResult,
    BasketSummaryCard,
    CompareRequest,
    CompareResponse,
    GroceryCategory,
    ItemSelectionResult,
    MatchQuality,
    MissingItemCandidate,
    MissingItemDetail,
    MixedBasketResult,
    SavingsExplanation,
    Supermarket,
    SupermarketBasketTotal,
    SupermarketProduct,
    build_intent,
)
from app.services.item_parser import parse_item_input
from app.services.seed_catalog import COMMON_KEYWORD_MAP, SEEDED_SUPERMARKETS

logger = logging.getLogger(__name__)
PREMIUM_PENALTY = Decimal("0.18")
SIZE_MISMATCH_PENALTY = Decimal("0.22")
WEAK_SUBSTITUTE_PENALTY = Decimal("0.25")

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


def _intent_from_item(parsed_item):
    category = _categorize(parsed_item.name)
    keywords = COMMON_KEYWORD_MAP.get(category, [parsed_item.name.lower()])
    expanded = sorted({_normalize_token(kw) for kw in keywords}.union(_expand_tokens(parsed_item.name)))
    if parsed_item.brand:
        expanded.append(_normalize_token(parsed_item.brand))
    expanded.extend(_normalize_token(tag) for tag in parsed_item.preferenceTags)
    return build_intent(parsed_item.name, parsed_item.quantity, category, sorted(set(expanded)))


def _score_overlap(intent_tokens: set[str], product: SupermarketProduct) -> tuple[int, list[str]]:
    searchable = " ".join([product.name, product.subcategory, product.category.value, *product.tags]).lower()
    product_tokens = _expand_tokens(searchable)
    hits = sorted(intent_tokens.intersection(product_tokens))
    return len(hits), hits


def _similarity_score(a: str, b: str) -> Decimal:
    return Decimal(str(round(SequenceMatcher(None, a, b).ratio(), 3)))


def _rank_candidate(intent, product: SupermarketProduct):
    reasons: list[str] = []
    tradeoffs: list[str] = []
    intent_tokens = set(intent.acceptedKeywords)

    if intent.category != GroceryCategory.unknown and product.category != intent.category:
        return None

    quality = MatchQuality.exact if product.category == intent.category else MatchQuality.acceptableEquivalent
    score = Decimal("0.30")
    confidence = Decimal("0.35")

    token_score, hits = _score_overlap(intent_tokens, product)
    if token_score:
        token_boost = Decimal(min(token_score, 6)) * Decimal("0.09")
        score += token_boost
        confidence += token_boost / 2
        reasons.append(f"Matched tokens ({token_score}): {', '.join(hits[:5])}.")
    else:
        reasons.append("No token overlap across name/tags/category/subcategory.")

    if intent.normalizedInput in product.name.lower():
        score += Decimal("0.2")
        confidence += Decimal("0.15")
        reasons.append("Direct phrase match in product name.")
    else:
        fuzzy = _similarity_score(intent.normalizedInput, product.name.lower())
        if fuzzy >= Decimal("0.64"):
            score += fuzzy * Decimal("0.20")
            confidence += Decimal("0.06")
            reasons.append(f"Fuzzy name similarity {fuzzy}.")

    if product.isOwnBrand:
        score += Decimal("0.03")
        reasons.append("Own-brand value signal applied.")

    if intent.category == GroceryCategory.unknown and token_score < 2 and intent.normalizedInput not in product.name.lower():
        reasons.append("Rejected: weak unknown-category match.")
        return None

    if token_score <= 1 and intent.category == GroceryCategory.unknown:
        quality = MatchQuality.weakSubstitute
        score -= WEAK_SUBSTITUTE_PENALTY
        tradeoffs.append("Low-confidence substitute due to weak category intent.")

    if product.isPremium:
        score -= PREMIUM_PENALTY
        tradeoffs.append("Premium product penalty applied.")

    if any(size_token in intent.normalizedInput for size_token in ["kg", "g", "l", "ml"]) and product.size not in intent.normalizedInput:
        score -= SIZE_MISMATCH_PENALTY
        tradeoffs.append("Requested size differs from candidate pack size.")

    confidence = max(Decimal("0.05"), min(Decimal("0.99"), confidence))
    score = max(Decimal("0.01"), min(Decimal("1.50"), score))
    reasons.append(f"Unit comparison basis: {product.unitDescription} {product.unitValue}.")
    return quality, confidence, score, hits, reasons, tradeoffs


def _selection(intent, supermarket: Supermarket, product: SupermarketProduct, quality: MatchQuality, confidence: Decimal, score: Decimal, matched_tokens: list[str], reasons: list[str], tradeoffs: list[str]) -> ItemSelectionResult:
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
        score=score,
        matchedTokens=matched_tokens,
        reasons=reasons,
        tradeoffs=tradeoffs,
    )


def _missing_explanation(unavailable_items) -> str:
    if not unavailable_items:
        return "All requested items were matched."
    item_names = ", ".join(intent.userInput for intent in unavailable_items)
    return f"Missing {len(unavailable_items)} item(s): {item_names}. Try broader names, category hints, or add more supermarkets."


def _build_market_total(supermarket: Supermarket, intents, inventory: list[SupermarketProduct]) -> SupermarketBasketTotal:
    selections: list[ItemSelectionResult] = []
    unavailable = []
    missing_details: list[MissingItemDetail] = []

    for intent in intents:
        ranked: list[tuple[MatchQuality, Decimal, Decimal, SupermarketProduct, list[str], list[str], list[str]]] = []
        for product in inventory:
            scored = _rank_candidate(intent, product)
            if scored is None:
                continue
            quality, confidence, score, matched_tokens, reasons, tradeoffs = scored
            ranked.append((quality, confidence, score, product, matched_tokens, reasons, tradeoffs))

        ranked.sort(key=lambda item: (-item[2], -item[0].value, item[3].price, item[3].unitValue))

        if not ranked:
            unavailable.append(intent)
            loose: list[MissingItemCandidate] = []
            for product in inventory:
                if intent.category != GroceryCategory.unknown and product.category != intent.category:
                    continue
                fuzzy_score = _similarity_score(intent.normalizedInput, product.name.lower())
                if fuzzy_score >= Decimal("0.45"):
                    loose.append(
                        MissingItemCandidate(
                            supermarketName=supermarket.name,
                            productName=product.name,
                            score=fuzzy_score,
                            reason=f"Name similarity {fuzzy_score}",
                        )
                    )
            missing_details.append(
                MissingItemDetail(
                    intent=intent,
                    reason="No candidate passed quality threshold.",
                    closeCandidates=sorted(loose, key=lambda item: item.score, reverse=True)[:3],
                    suggestion="Try adding brand, size, or simpler wording.",
                )
            )
            logger.info("no-match supermarket=%s item=%s category=%s reason=no candidates survived filters", supermarket.name, intent.userInput, intent.category.value)
            continue

        quality, confidence, score, product, matched_tokens, reasons, tradeoffs = ranked[0]
        if score < Decimal("0.30"):
            unavailable.append(intent)
            missing_details.append(
                MissingItemDetail(
                    intent=intent,
                    reason=f"Best candidate score {score} below acceptance threshold.",
                    closeCandidates=[
                        MissingItemCandidate(
                            supermarketName=supermarket.name,
                            productName=candidate[3].name,
                            score=candidate[2],
                            reason="Candidate was close but lower confidence.",
                        )
                        for candidate in ranked[:3]
                    ],
                    suggestion="Add preferred brand or approximate size (e.g. 500g).",
                )
            )
            continue
        selections.append(_selection(intent, supermarket, product, quality, confidence, score, matched_tokens, reasons, tradeoffs))
        debug_top = [f"{candidate[3].name}(score={candidate[2]})" for candidate in ranked[:3]]
        logger.info(
            "match supermarket=%s item=%s product=%s quality=%s confidence=%s score=%s candidates=%s",
            supermarket.name,
            intent.userInput,
            product.name,
            quality.name,
            confidence,
            score,
            " | ".join(debug_top),
        )

    return SupermarketBasketTotal(
        id=uuid4(),
        supermarket=supermarket,
        selections=selections,
        unavailableItems=unavailable,
        missingItemsExplanation=_missing_explanation(unavailable),
        missingItemDetails=missing_details,
        total=sum((item.totalPrice for item in selections), Decimal("0.00")),
    )


def _best_options_per_intent(intents, totals: Iterable[SupermarketBasketTotal]):
    for intent in intents:
        options = [selection for total in totals for selection in total.selections if selection.intent.id == intent.id]
        best = min(options, key=lambda option: (option.totalPrice, -option.score, -option.matchQuality.value, -option.confidence)) if options else None
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
                selections.append(min(constrained, key=lambda option: (option.totalPrice, -option.score, -option.matchQuality.value, -option.confidence)))
    else:
        for _, best in _best_options_per_intent(intents, totals):
            if best:
                selections.append(best)

    unavailable = [intent for intent in intents if not any(selection.intent.id == intent.id for selection in selections)]
    unavailable_ids = {intent.id for intent in unavailable}
    combined_missing = [detail for total in totals for detail in total.missingItemDetails if detail.intent.id in unavailable_ids]
    return MixedBasketResult(
        selections=selections,
        unavailableItems=unavailable,
        missingItemsExplanation=_missing_explanation(unavailable),
        missingItemDetails=combined_missing,
        total=sum((item.totalPrice for item in selections), Decimal("0.00")),
    )




def _best_convenience_basket(intents, totals: list[SupermarketBasketTotal]) -> MixedBasketResult:
    if not totals:
        return MixedBasketResult(selections=[], unavailableItems=intents, total=Decimal("0.00"), missingItemsExplanation=_missing_explanation(intents))

    best_total = None
    best_score = None
    for candidate in totals:
        # convenience strongly prioritises complete baskets at one store
        penalty = Decimal(len(candidate.unavailableItems)) * Decimal("5.00")
        score = candidate.total + penalty
        if best_score is None or score < best_score:
            best_score = score
            best_total = candidate

    assert best_total is not None
    return MixedBasketResult(
        selections=best_total.selections,
        unavailableItems=best_total.unavailableItems,
        total=best_total.total,
        missingItemsExplanation=best_total.missingItemsExplanation,
        missingItemDetails=best_total.missingItemDetails,
    )

def build_comparison(request: CompareRequest) -> CompareResponse:
    product_map = _seeded_product_map()
    intents = []
    for item in request.shoppingList.items:
        parsed = parse_item_input(item.name, fallback_quantity=item.quantity)
        intents.append(_intent_from_item(parsed))

    totals = []
    for supermarket in request.supermarkets:
        inventory = product_map.get(supermarket.name.lower(), [])
        totals.append(_build_market_total(supermarket, intents, inventory))

    totals = sorted(totals, key=lambda x: x.total)
    cheapest_single = next((total for total in totals if not total.unavailableItems), totals[0] if totals else None)

    max_supermarkets = request.maxSupermarkets if getattr(request, "maxSupermarkets", None) else None
    mixed = _build_mixed_basket(intents, totals, max_supermarkets=max_supermarkets)
    convenience = _best_convenience_basket(intents, totals)

    selected = mixed if request.comparisonMode.value == "cheapestPossible" else MixedBasketResult(
        selections=cheapest_single.selections if cheapest_single else [],
        unavailableItems=cheapest_single.unavailableItems if cheapest_single else intents,
        missingItemsExplanation=cheapest_single.missingItemsExplanation if cheapest_single else _missing_explanation(intents),
        missingItemDetails=cheapest_single.missingItemDetails if cheapest_single else [],
        total=cheapest_single.total if cheapest_single else Decimal("0.00"),
    )

    result = BasketOptimisationResult(
        shoppingList=request.shoppingList,
        intents=intents,
        supermarketTotals=totals,
        cheapestSingleStore=cheapest_single,
        mixedBasket=mixed,
        bestConvenienceBasket=convenience,
        selectedBasket=selected,
        comparisonMode=request.comparisonMode,
        preferences=request.preferences,
        maxSupermarkets=max_supermarkets,
        summaryCards=[
            BasketSummaryCard(title="Cheapest mixed basket", total=mixed.total, subtitle="Lowest total across stores"),
            BasketSummaryCard(title="Cheapest single-store basket", total=cheapest_single.total if cheapest_single else Decimal("0.00"), subtitle=cheapest_single.supermarket.name if cheapest_single else "No complete store"),
            BasketSummaryCard(title="Best convenience option", total=convenience.total, subtitle="Fewest missing items at one store"),
        ],
    )

    most_expensive_total = totals[-1].total if totals else Decimal("0.00")
    savings_vs_most_expensive = most_expensive_total - selected.total
    savings_vs_cheapest_single = (cheapest_single.total - selected.total) if cheapest_single else Decimal("0.00")

    logger.info("analytics event=compare_completed items=%s supermarkets=%s selected_total=%s mixed_total=%s convenience_total=%s", len(request.shoppingList.items), len(request.supermarkets), selected.total, mixed.total, convenience.total)

    return CompareResponse(
        result=result,
        savingsVsMostExpensive=savings_vs_most_expensive,
        savingsVsCheapestSingleStore=savings_vs_cheapest_single,
        savingsExplanation=SavingsExplanation(
            amountVsMostExpensive=savings_vs_most_expensive,
            amountVsCheapestSingleStore=savings_vs_cheapest_single,
            explanation=f"Selected basket saves £{savings_vs_most_expensive:.2f} vs most expensive and £{savings_vs_cheapest_single:.2f} vs cheapest single-store.",
        ),
    )
