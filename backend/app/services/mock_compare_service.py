from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from difflib import SequenceMatcher
from itertools import combinations
from typing import Iterable
from uuid import uuid4

from app.models import (
    BasketDecisionMode,
    BasketOptimisationResult,
    BasketStrategyResult,
    BasketSummaryCard,
    CompareRequest,
    CompareResponse,
    GroceryCategory,
    ItemSelectionResult,
    MatchQuality,
    MissingItemCandidate,
    MissingItemDetail,
    MixedBasketResult,
    MissingItemsSummary,
    PurchasePlan,
    PurchasePlanItem,
    SavingsExplanation,
    SavingsSummary,
    StoreAllocationSummary,
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
SIZE_NEAR_MISS_PENALTY = Decimal("0.08")

SYNONYM_MAP: dict[str, list[str]] = {
    "beanz": ["beans", "baked beans"],
    "yoghurt": ["yogurt"],
    "fillets": ["fillet", "breast"],
    "loaf": ["bread"],
}

@dataclass
class PreferenceContext:
    own_brand_preferred: bool = False
    branded_preferred: bool = False
    branded_only: bool = False
    avoid_premium: bool = False
    organic_only: bool = False
    max_supermarkets: int | None = None
    selected_supermarkets: list[str] | None = None
    effects: list[str] | None = None


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


def _parse_size_token(text: str) -> tuple[Decimal | None, str | None]:
    normalized = text.lower().replace(" ", "")
    units = ("kg", "g", "ml", "l")
    for unit in units:
        idx = normalized.find(unit)
        if idx <= 0:
            continue
        value_str = "".join(ch for ch in normalized[:idx] if ch.isdigit() or ch == ".")
        if not value_str:
            continue
        try:
            return Decimal(value_str), unit
        except Exception:
            return None, None
    return None, None


def _size_similarity(intent_text: str, product_size: str) -> tuple[Decimal, str]:
    requested_value, requested_unit = _parse_size_token(intent_text)
    candidate_value, candidate_unit = _parse_size_token(product_size)
    if requested_value is None or candidate_value is None or requested_unit != candidate_unit:
        return Decimal("0.35"), "No directly comparable size token; neutral size confidence applied."
    if requested_value == 0:
        return Decimal("0.35"), "No usable requested size value."
    ratio = candidate_value / requested_value
    if Decimal("0.9") <= ratio <= Decimal("1.1"):
        return Decimal("1.00"), f"Size closely matches requested amount ({requested_value}{requested_unit})."
    if Decimal("0.7") <= ratio <= Decimal("1.3"):
        return Decimal("0.70"), f"Size is near requested amount ({candidate_value}{candidate_unit} vs {requested_value}{requested_unit})."
    return Decimal("0.10"), f"Size differs materially ({candidate_value}{candidate_unit} vs {requested_value}{requested_unit})."


def _rank_candidate(intent, product: SupermarketProduct, preferences: PreferenceContext):
    reasons: list[str] = []
    tradeoffs: list[str] = []
    intent_tokens = set(intent.acceptedKeywords)

    if intent.category != GroceryCategory.unknown and product.category != intent.category:
        return None

    quality = MatchQuality.exact if product.category == intent.category else MatchQuality.acceptableEquivalent
    score = Decimal("0.00")
    confidence = Decimal("0.00")

    token_score, hits = _score_overlap(intent_tokens, product)
    name_similarity = _similarity_score(intent.normalizedInput, product.name.lower())
    category_similarity = Decimal("1.0") if product.category == intent.category and intent.category != GroceryCategory.unknown else (Decimal("0.5") if intent.category == GroceryCategory.unknown else Decimal("0.0"))
    size_similarity, size_reason = _size_similarity(intent.normalizedInput, product.size)
    brand_similarity = Decimal("0.55")
    price_sanity = Decimal("1.0")

    if token_score:
        reasons.append(f"Matched tokens ({token_score}): {', '.join(hits[:5])}.")
    else:
        reasons.append("No token overlap across name/tags/category/subcategory.")

    if intent.normalizedInput in product.name.lower():
        name_similarity = max(name_similarity, Decimal("1.0"))
        reasons.append("Direct phrase match in product name.")
    elif name_similarity >= Decimal("0.64"):
        reasons.append(f"Fuzzy name similarity {name_similarity}.")

    if intent.category != GroceryCategory.unknown and product.category != intent.category:
        reasons.append("Rejected: wrong product category for request.")
        return None
    reasons.append(size_reason)

    if product.isOwnBrand:
        brand_similarity = Decimal("0.65")
        reasons.append("Own-brand value signal applied.")
    if preferences.own_brand_preferred:
        if product.isOwnBrand:
            brand_similarity = min(Decimal("1.0"), brand_similarity + Decimal("0.35"))
            reasons.append("Own-brand preference applied.")
        else:
            brand_similarity = Decimal("0.25")
            tradeoffs.append("Non-own-brand product deprioritised.")
    if preferences.branded_preferred:
        if not product.isOwnBrand:
            brand_similarity = Decimal("0.92")
            reasons.append("Branded preference applied.")
        else:
            brand_similarity = Decimal("0.20")
            tradeoffs.append("Own-brand item deprioritised for branded preference.")
    if preferences.branded_only and product.isOwnBrand:
        reasons.append("Rejected: branded-only preference.")
        return None

    if intent.category == GroceryCategory.unknown and token_score < 2 and intent.normalizedInput not in product.name.lower():
        reasons.append("Rejected: weak unknown-category match.")
        return None

    if token_score <= 1 and intent.category == GroceryCategory.unknown:
        quality = MatchQuality.weakSubstitute
        score -= WEAK_SUBSTITUTE_PENALTY
        tradeoffs.append("Low-confidence substitute due to weak category intent.")

    if product.isPremium:
        price_sanity -= Decimal("0.22")
        tradeoffs.append("Premium product penalty applied.")
    if preferences.avoid_premium and product.isPremium:
        score -= Decimal("0.45")
        reasons.append("Premium products excluded by preference.")
        return None
    if preferences.organic_only and not product.isOrganic:
        reasons.append("Rejected: organic-only preference.")
        return None

    if size_similarity <= Decimal("0.10"):
        score -= SIZE_MISMATCH_PENALTY
        tradeoffs.append("Requested size differs from candidate pack size.")
    elif size_similarity < Decimal("1.0"):
        score -= SIZE_NEAR_MISS_PENALTY

    score += (name_similarity * Decimal("0.38"))
    score += (category_similarity * Decimal("0.18"))
    score += (size_similarity * Decimal("0.22"))
    score += (brand_similarity * Decimal("0.14"))
    score += (price_sanity * Decimal("0.08"))
    confidence = score

    confidence = max(Decimal("0.05"), min(Decimal("0.99"), confidence))
    score = max(Decimal("0.01"), min(Decimal("1.50"), score))
    reasons.append(f"Unit comparison basis: {product.unitDescription} {product.unitValue}.")
    return quality, confidence, score, hits, reasons, tradeoffs


def _selection(intent, supermarket: Supermarket, product: SupermarketProduct, quality: MatchQuality, confidence: Decimal, score: Decimal, matched_tokens: list[str], reasons: list[str], tradeoffs: list[str]) -> ItemSelectionResult:
    quantity = intent.quantity
    total = product.price * Decimal(quantity)
    if confidence >= Decimal("0.85") and quality == MatchQuality.exact:
        match_type = "exact"
        confidence_label = "high"
    elif confidence >= Decimal("0.60"):
        match_type = "close"
        confidence_label = "medium"
    else:
        match_type = "approximate"
        confidence_label = "low"
    match_explanation = reasons[0] if reasons else "Chosen as strongest available candidate."
    selection_reason = f"Chosen for best weighted score ({score}) balancing name/category/size/brand/price checks."
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
        matchType=match_type,
        confidenceLabel=confidence_label,
        score=score,
        matchedTokens=matched_tokens,
        reasons=reasons,
        matchExplanation=match_explanation,
        selectionReason=selection_reason,
        tradeoffs=tradeoffs,
    )


def _missing_explanation(unavailable_items) -> str:
    if not unavailable_items:
        return "All requested items were matched."
    item_names = ", ".join(intent.userInput for intent in unavailable_items)
    return f"Missing {len(unavailable_items)} item(s): {item_names}. Try broader names, category hints, or add more supermarkets."


def _build_market_total(supermarket: Supermarket, intents, inventory: list[SupermarketProduct], preferences: PreferenceContext) -> SupermarketBasketTotal:
    selections: list[ItemSelectionResult] = []
    unavailable = []
    missing_details: list[MissingItemDetail] = []

    for intent in intents:
        ranked: list[tuple[MatchQuality, Decimal, Decimal, SupermarketProduct, list[str], list[str], list[str]]] = []
        for product in inventory:
            scored = _rank_candidate(intent, product, preferences)
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
            if score >= Decimal("0.22"):
                tradeoffs.append("Approximate fallback selected because no high-confidence candidate was available.")
                if quality != MatchQuality.exact:
                    quality = MatchQuality.weakSubstitute
                reasons.append(f"Fallback accepted: best available option had score {score}.")
            else:
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
    if not totals:
        return MixedBasketResult(
            selections=[],
            unavailableItems=intents,
            missingItemsExplanation=_missing_explanation(intents),
            missingItemDetails=[],
            total=Decimal("0.00"),
            storesUsed=0,
        )

    max_store_cap = max_supermarkets if max_supermarkets and max_supermarkets > 0 else len(totals)
    max_store_cap = min(max_store_cap, len(totals))

    def build_for_subset(allowed_stores: set[str]) -> MixedBasketResult:
        selections: list[ItemSelectionResult] = []
        for intent in intents:
            candidates = [
                selection
                for total in totals
                if total.supermarket.name in allowed_stores
                for selection in total.selections
                if selection.intent.id == intent.id
            ]
            if candidates:
                selections.append(
                    min(
                        candidates,
                        key=lambda option: (option.totalPrice, -option.score, -option.matchQuality.value, -option.confidence),
                    )
                )
        unavailable = [intent for intent in intents if not any(selection.intent.id == intent.id for selection in selections)]
        unavailable_ids = {intent.id for intent in unavailable}
        combined_missing = [detail for total in totals for detail in total.missingItemDetails if detail.intent.id in unavailable_ids]
        stores_used = len({item.supermarket.name for item in selections})
        return MixedBasketResult(
            selections=selections,
            unavailableItems=unavailable,
            missingItemsExplanation=_missing_explanation(unavailable),
            missingItemDetails=combined_missing,
            total=sum((item.totalPrice for item in selections), Decimal("0.00")),
            storesUsed=stores_used,
        )

    all_store_names = [total.supermarket.name for total in totals]
    candidate_baskets: list[MixedBasketResult] = []
    for size in range(1, max_store_cap + 1):
        for subset in combinations(all_store_names, size):
            candidate_baskets.append(build_for_subset(set(subset)))

    def objective(basket: MixedBasketResult) -> Decimal:
        missing_penalty = Decimal(len(basket.unavailableItems)) * Decimal("8.50")
        store_penalty = Decimal(max(0, basket.storesUsed - 1)) * Decimal("0.95")
        return basket.total + missing_penalty + store_penalty

    return min(candidate_baskets, key=lambda basket: (objective(basket), basket.total))




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
        storesUsed=1 if best_total.selections else 0,
    )


def _single_store_as_mixed(candidate: SupermarketBasketTotal | None, intents) -> MixedBasketResult:
    if not candidate:
        return MixedBasketResult(
            selections=[],
            unavailableItems=intents,
            total=Decimal("0.00"),
            storesUsed=0,
            missingItemsExplanation=_missing_explanation(intents),
            missingItemDetails=[],
        )
    return MixedBasketResult(
        selections=candidate.selections,
        unavailableItems=candidate.unavailableItems,
        total=candidate.total,
        storesUsed=1 if candidate.selections else 0,
        missingItemsExplanation=candidate.missingItemsExplanation,
        missingItemDetails=candidate.missingItemDetails,
    )


def _allocation_summary(selections: list[ItemSelectionResult]) -> list[StoreAllocationSummary]:
    by_store: dict[str, list[ItemSelectionResult]] = {}
    for selection in selections:
        by_store.setdefault(selection.supermarket.name, []).append(selection)
    return [
        StoreAllocationSummary(
            storeName=store,
            itemCount=len(items),
            totalSpend=sum((item.totalPrice for item in items), Decimal("0.00")),
        )
        for store, items in sorted(by_store.items(), key=lambda item: item[0])
    ]


def _build_purchase_plan_items(intents, selections: list[ItemSelectionResult], unavailable_items) -> list[PurchasePlanItem]:
    selected_by_intent = {selection.intent.id: selection for selection in selections}
    unavailable_ids = {intent.id for intent in unavailable_items}
    items: list[PurchasePlanItem] = []
    for intent in intents:
        selected = selected_by_intent.get(intent.id)
        if selected:
            items.append(
                PurchasePlanItem(
                    originalUserItem=intent,
                    selectedProduct=selected.product,
                    selectedStore=selected.supermarket,
                    quantity=selected.quantity,
                    price=selected.totalPrice,
                    explanation="Selected as best available option for this strategy.",
                    matchConfidence=selected.confidence,
                )
            )
            continue
        if intent.id in unavailable_ids:
            items.append(
                PurchasePlanItem(
                    originalUserItem=intent,
                    quantity=intent.quantity,
                    price=Decimal("0.00"),
                    explanation="No suitable product could be matched for this item in the chosen strategy.",
                )
            )
    return items


def _build_missing_summary(unavailable_items) -> MissingItemsSummary:
    return MissingItemsSummary(
        count=len(unavailable_items),
        itemNames=[item.userInput for item in unavailable_items],
        explanation=_missing_explanation(unavailable_items),
    )


def _build_strategy_results(
    intents,
    totals: list[SupermarketBasketTotal],
    cheapest_single: SupermarketBasketTotal | None,
    mixed: MixedBasketResult,
    convenience: MixedBasketResult,
    max_two: MixedBasketResult,
    preference_effects: list[str],
) -> list[BasketStrategyResult]:
    cheapest_total = mixed.total
    cheapest_single_total = cheapest_single.total if cheapest_single else Decimal("0.00")
    most_expensive_single_total = totals[-1].total if totals else Decimal("0.00")
    single_plan = _single_store_as_mixed(cheapest_single, intents)
    candidates = [
        (BasketDecisionMode.cheapestSingleStore, single_plan),
        (BasketDecisionMode.cheapestMixedBasket, mixed),
        (BasketDecisionMode.bestConvenienceOption, convenience),
        (BasketDecisionMode.cheapestMixedBasketMaxTwoStores, max_two),
    ]

    results: list[BasketStrategyResult] = []
    for mode, basket in candidates:
        price_delta = basket.total - cheapest_total
        missing_penalty = Decimal(len(basket.unavailableItems)) * Decimal("12.00")
        score = basket.total + (Decimal(basket.storesUsed) * Decimal("4.00")) + missing_penalty
        if mode == BasketDecisionMode.bestConvenienceOption:
            score = score - Decimal("2.00")
        tradeoffs = [
            f"Uses {basket.storesUsed} store(s).",
            f"Missing {len(basket.unavailableItems)} item(s).",
            f"Costs £{price_delta:.2f} more than the cheapest mixed basket." if price_delta >= 0 else f"Saves £{abs(price_delta):.2f} vs cheapest mixed basket.",
        ]
        tradeoffs.extend(preference_effects)
        won_because = (
            "Lowest total cost across all item-level allocations."
            if mode == BasketDecisionMode.cheapestMixedBasket
            else "Complete basket at one supermarket with best single-store price."
            if mode == BasketDecisionMode.cheapestSingleStore
            else "Balanced fewer-store convenience with reasonable price."
            if mode == BasketDecisionMode.bestConvenienceOption
            else "Limits shopping to at most two stores while keeping cost low."
        )
        stores_used = sorted({selection.supermarket.name for selection in basket.selections})
        savings = SavingsSummary(
            versusCheapestMixedBasket=cheapest_total - basket.total,
            versusCheapestSingleStore=cheapest_single_total - basket.total,
            versusMostExpensiveSingleStore=most_expensive_single_total - basket.total,
            explanation=(
                f"Compared with alternatives: £{(cheapest_total - basket.total):.2f} vs mixed, "
                f"£{(cheapest_single_total - basket.total):.2f} vs single-store, "
                f"£{(most_expensive_single_total - basket.total):.2f} vs most expensive single-store."
            ),
        )
        plan_items = _build_purchase_plan_items(intents, basket.selections, basket.unavailableItems)
        missing_summary = _build_missing_summary(basket.unavailableItems)
        explanation = (
            f"{won_because} Uses {len(stores_used)} store(s), total £{basket.total:.2f}, "
            f"and leaves {missing_summary.count} item(s) unmatched."
        )
        tradeoff_summary = " | ".join(tradeoffs)
        results.append(
            BasketStrategyResult(
                mode=mode,
                plan=PurchasePlan(
                    mode=mode,
                    basket=basket,
                    items=plan_items,
                    allocation=_allocation_summary(basket.selections),
                    savings=savings,
                    missingItems=missing_summary,
                    unavailableItemsCount=len(basket.unavailableItems),
                ),
                totalPrice=basket.total,
                storesUsed=stores_used,
                storeCount=len(stores_used),
                savings=savings,
                missingItemsCount=missing_summary.count,
                chosenItems=plan_items,
                explanation=explanation,
                tradeoffSummary=tradeoff_summary,
                wonBecause=won_because,
                tradeoffs=tradeoffs,
                score=score,
            )
        )
    return results

def build_comparison(request: CompareRequest) -> CompareResponse:
    preference_effects: list[str] = []
    parsed_preferences = set()
    product_map = _seeded_product_map()
    intents = []
    for item in request.shoppingList.items:
        parsed = parse_item_input(item.name, fallback_quantity=item.quantity)
        parsed_preferences.update(parsed.preferenceTags)
        intents.append(_intent_from_item(parsed))

    own_brand_preferred = request.preferences.brandPreference.value == "ownBrandPreferred" or "own brand" in parsed_preferences or "own" in parsed_preferences
    branded_only = request.preferences.brandPreference.value == "brandedOnly" or "branded only" in parsed_preferences
    branded_preferred = request.preferences.brandPreference.value == "brandedPreferred" or "branded" in parsed_preferences
    avoid_premium = request.preferences.avoidPremium or "avoid premium" in parsed_preferences
    organic_only = request.preferences.organicOnly or "organic only" in parsed_preferences or "organic" in parsed_preferences

    if own_brand_preferred:
        preference_effects.append("Own-brand preference applied")
    if branded_preferred:
        preference_effects.append("Branded preference applied")
    if branded_only:
        preference_effects.append("Branded-only filter applied")
    if avoid_premium:
        preference_effects.append("Premium products excluded")
    if organic_only:
        preference_effects.append("Organic-only filter applied")
    if request.supermarkets:
        preference_effects.append(f"Limited to selected supermarkets ({', '.join(market.name for market in request.supermarkets)})")

    totals = []
    preference_context = PreferenceContext(
        own_brand_preferred=own_brand_preferred,
        branded_preferred=branded_preferred,
        branded_only=branded_only,
        avoid_premium=avoid_premium,
        organic_only=organic_only,
        max_supermarkets=request.maxSupermarkets,
        selected_supermarkets=[market.name for market in request.supermarkets],
        effects=preference_effects,
    )
    for supermarket in request.supermarkets:
        inventory = product_map.get(supermarket.name.lower(), [])
        totals.append(_build_market_total(supermarket, intents, inventory, preference_context))

    totals = sorted(totals, key=lambda x: x.total)
    cheapest_single = next((total for total in totals if not total.unavailableItems), totals[0] if totals else None)

    max_supermarkets = request.maxSupermarkets if getattr(request, "maxSupermarkets", None) else None
    if max_supermarkets:
        preference_effects.append(f"Limited to {max_supermarkets} store{'s' if max_supermarkets != 1 else ''}")
    mixed = _build_mixed_basket(intents, totals, max_supermarkets=max_supermarkets)
    max_two = _build_mixed_basket(intents, totals, max_supermarkets=2)
    convenience = _best_convenience_basket(intents, totals)
    strategy_results = _build_strategy_results(intents, totals, cheapest_single, mixed, convenience, max_two, preference_effects)

    selected = mixed if request.comparisonMode.value == "cheapestPossible" else _single_store_as_mixed(cheapest_single, intents)
    if request.comparisonMode.value == "bestConvenienceOption":
        selected = convenience
    selected_strategy_mode = (
        BasketDecisionMode.cheapestMixedBasket
        if request.comparisonMode.value == "cheapestPossible"
        else BasketDecisionMode.bestConvenienceOption
        if request.comparisonMode.value == "bestConvenienceOption"
        else BasketDecisionMode.cheapestSingleStore
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
        preferenceEffects=preference_effects,
        summaryCards=[
            BasketSummaryCard(title="Cheapest mixed basket", total=mixed.total, subtitle="Lowest total across stores"),
            BasketSummaryCard(title="Cheapest single-store basket", total=cheapest_single.total if cheapest_single else Decimal("0.00"), subtitle=cheapest_single.supermarket.name if cheapest_single else "No complete store"),
            BasketSummaryCard(title="Best convenience option", total=convenience.total, subtitle=f"{convenience.storesUsed} store(s), practical balance"),
        ],
        strategyResults=strategy_results,
        selectedStrategyMode=selected_strategy_mode,
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
