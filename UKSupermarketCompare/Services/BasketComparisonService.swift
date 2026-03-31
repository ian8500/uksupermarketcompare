import Foundation

protocol BasketOptimising {
    func optimise(
        shoppingList: ShoppingList,
        supermarkets: [Supermarket],
        mode: BasketComparisonMode,
        preferences: BasketUserPreferences
    ) -> BasketOptimisationResult
}

final class BasketOptimiserService: BasketOptimising {
    private let dataProvider: SupermarketDataProviding

    init(dataProvider: SupermarketDataProviding) {
        self.dataProvider = dataProvider
    }

    func optimise(
        shoppingList: ShoppingList,
        supermarkets: [Supermarket],
        mode: BasketComparisonMode,
        preferences: BasketUserPreferences
    ) -> BasketOptimisationResult {
        let intents = shoppingList.items.map(resolveIntent)
        let totals = supermarkets.map { buildSupermarketTotal(for: $0, intents: intents, preferences: preferences) }
            .sorted { $0.total < $1.total }

        let mixedSelections: [ItemSelectionResult] = intents.compactMap { intent in
            let options = totals.compactMap { total in
                total.selections.first(where: { $0.intent.id == intent.id })
            }
            return options.min { lhs, rhs in
                if lhs.totalPrice == rhs.totalPrice {
                    return lhs.confidence > rhs.confidence
                }
                return lhs.totalPrice < rhs.totalPrice
            }
        }

        let unavailable = intents.filter { intent in
            !mixedSelections.contains(where: { $0.intent.id == intent.id })
        }

        let mixed = MixedBasketResult(selections: mixedSelections, unavailableItems: unavailable)
        let cheapestSingle = totals.first(where: { $0.unavailableItems.isEmpty })
        let selectedBasket: MixedBasketResult

        switch mode {
        case .cheapestPossible:
            selectedBasket = mixed
        case .cheapestSingleStoreOnly:
            if let cheapestSingle {
                selectedBasket = MixedBasketResult(selections: cheapestSingle.selections, unavailableItems: cheapestSingle.unavailableItems)
            } else {
                selectedBasket = mixed
            }
        }

        return BasketOptimisationResult(
            shoppingList: shoppingList,
            intents: intents,
            supermarketTotals: totals,
            cheapestSingleStore: cheapestSingle,
            mixedBasket: mixed,
            selectedBasket: selectedBasket,
            comparisonMode: mode,
            preferences: preferences
        )
    }

    private func resolveIntent(item: ShoppingItem) -> GroceryIntent {
        let normalized = item.name.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let category: GroceryCategory

        switch normalized {
        case let value where value.contains("milk"): category = .milk
        case let value where value.contains("bread") || value.contains("loaf"): category = .bread
        case let value where value.contains("egg"): category = .eggs
        case let value where value.contains("butter") || value.contains("spread"): category = .butter
        case let value where value.contains("pasta") || value.contains("spaghetti") || value.contains("penne") || value.contains("fusilli"): category = .pasta
        case let value where value.contains("bean"): category = .bakedBeans
        case let value where value.contains("banana"): category = .bananas
        case let value where value.contains("chicken"): category = .chickenBreast
        case let value where value.contains("cereal") || value.contains("flakes") || value.contains("muesli") || value.contains("granola"): category = .cereal
        case let value where value.contains("cheese") || value.contains("cheddar") || value.contains("mozzarella"): category = .cheese
        case let value where value.contains("tomato"): category = .tomatoes
        case let value where value.contains("rice"): category = .rice
        case let value where value.contains("yogurt") || value.contains("yoghurt"): category = .yogurt
        case let value where value.contains("apple"): category = .apples
        default: category = .unknown
        }

        return GroceryIntent(userInput: item.name, category: category, quantity: item.quantity)
    }

    private func buildSupermarketTotal(for supermarket: Supermarket, intents: [GroceryIntent], preferences: BasketUserPreferences) -> SupermarketBasketTotal {
        let products = dataProvider.products(at: supermarket)
        var selections: [ItemSelectionResult] = []
        var unavailable: [GroceryIntent] = []

        for intent in intents {
            let candidates = products.compactMap { candidate(for: intent, supermarket: supermarket, product: $0, preferences: preferences) }
                .filter(\.isValid)

            guard let best = candidates.min(by: candidateSort) else {
                unavailable.append(intent)
                continue
            }

            selections.append(
                ItemSelectionResult(
                    intent: intent,
                    supermarket: supermarket,
                    product: best.product,
                    matchQuality: best.matchQuality,
                    confidence: best.confidence,
                    reasons: best.reasons
                )
            )
        }

        return SupermarketBasketTotal(supermarket: supermarket, selections: selections, unavailableItems: unavailable)
    }

    private func candidateSort(lhs: ProductCandidate, rhs: ProductCandidate) -> Bool {
        if lhs.matchQuality != rhs.matchQuality {
            return lhs.matchQuality > rhs.matchQuality
        }
        if lhs.weightedUnitValue != rhs.weightedUnitValue {
            return lhs.weightedUnitValue < rhs.weightedUnitValue
        }
        if lhs.product.price != rhs.product.price {
            return lhs.product.price < rhs.product.price
        }
        return lhs.confidence > rhs.confidence
    }

    private func candidate(
        for intent: GroceryIntent,
        supermarket: Supermarket,
        product: SupermarketProduct,
        preferences: BasketUserPreferences
    ) -> ProductCandidate? {
        if intent.category != .unknown && product.category != intent.category { return nil }
        if preferences.organicOnly && !product.isOrganic { return nil }

        var quality: MatchQuality = .weakSubstitute
        var score = Decimal(0.20)
        var reasons: [String] = []

        if product.category == intent.category {
            quality = .exact
            score += 0.45
            reasons.append("Exact category match for \(intent.category.displayName.lowercased()).")
        }

        let keywordHits = intent.acceptedKeywords.filter {
            product.tags.contains($0) || product.name.lowercased().contains($0)
        }
        if !keywordHits.isEmpty {
            score += Decimal(min(keywordHits.count, 3)) * 0.08
            reasons.append("Matched keywords: \(keywordHits.prefix(3).joined(separator: ", ")).")
            if quality == .weakSubstitute {
                quality = .acceptableEquivalent
            }
        }

        switch preferences.brandPreference {
        case .ownBrandPreferred:
            if product.isOwnBrand {
                score += 0.10
                reasons.append("Own-brand preference matched.")
            } else {
                score -= 0.06
            }
        case .brandedPreferred:
            if !product.isOwnBrand {
                score += 0.10
                reasons.append("Branded preference matched.")
            } else {
                score -= 0.06
            }
        case .neutral:
            break
        }

        if preferences.avoidPremium && product.isPremium {
            score -= 0.15
            reasons.append("Premium item penalised due to preference.")
            if quality == .exact {
                quality = .acceptableEquivalent
            }
        }

        if product.isOrganic {
            score += 0.03
            reasons.append("Organic option available.")
        }

        if product.price <= 0 || product.unitValue <= 0 { return nil }

        let weightedUnit = max(Decimal(0.0001), product.unitValue - (score * 0.02))
        let finalScore = max(0.10, min(0.99, score))
        reasons.append("Compared using unit price (\(product.unitDescription)).")

        return ProductCandidate(
            id: UUID(),
            intent: intent,
            supermarket: supermarket,
            product: product,
            matchQuality: quality,
            confidence: finalScore,
            weightedUnitValue: weightedUnit,
            isValid: true,
            reasons: reasons
        )
    }
}
