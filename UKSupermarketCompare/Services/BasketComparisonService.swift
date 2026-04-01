import Foundation

protocol BasketOptimising {
    func optimise(
        shoppingList: ShoppingList,
        supermarkets: [Supermarket],
        mode: BasketComparisonMode,
        preferences: BasketUserPreferences,
        maxSupermarkets: Int?
    ) -> BasketOptimisationResult
}

final class BasketOptimiserService: BasketOptimising {
    private let dataProvider: SupermarketDataProviding
    private let groceryCatalogService: GroceryCatalogServing

    init(dataProvider: SupermarketDataProviding, groceryCatalogService: GroceryCatalogServing) {
        self.dataProvider = dataProvider
        self.groceryCatalogService = groceryCatalogService
    }

    func optimise(
        shoppingList: ShoppingList,
        supermarkets: [Supermarket],
        mode: BasketComparisonMode,
        preferences: BasketUserPreferences,
        maxSupermarkets: Int?
    ) -> BasketOptimisationResult {
        let intents = shoppingList.items.map(resolveIntent)
        let totals = supermarkets.map { buildSupermarketTotal(for: $0, intents: intents, preferences: preferences) }
            .sorted { $0.total < $1.total }

        let mixedSelections: [ItemSelectionResult] = intents.compactMap { intent in
            let options = totals.compactMap { total in
                total.selections.first(where: { $0.intent.id == intent.id })
            }
            let best = options.min { lhs, rhs in
                if lhs.totalPrice == rhs.totalPrice {
                    return lhs.confidence > rhs.confidence
                }
                return lhs.totalPrice < rhs.totalPrice
            }
            return best
        }
        let constrainedMixedSelections = constrainSelections(mixedSelections, maxSupermarkets: maxSupermarkets)

        let unavailable = intents.filter { intent in
            !constrainedMixedSelections.contains(where: { $0.intent.id == intent.id })
        }

        let mixed = MixedBasketResult(selections: constrainedMixedSelections, unavailableItems: unavailable)
        let cheapestSingle = totals.first(where: { $0.unavailableItems.isEmpty })
        let convenience = totals.min {
            let lhsScore = $0.total + Decimal($0.unavailableItems.count * 5)
            let rhsScore = $1.total + Decimal($1.unavailableItems.count * 5)
            return lhsScore < rhsScore
        }
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
        case .bestConvenienceOption:
            if let convenience {
                selectedBasket = MixedBasketResult(selections: convenience.selections, unavailableItems: convenience.unavailableItems)
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
            preferences: preferences,
            preferenceEffects: buildPreferenceEffects(preferences: preferences, maxSupermarkets: maxSupermarkets)
        )
    }

    private func buildPreferenceEffects(preferences: BasketUserPreferences, maxSupermarkets: Int?) -> [String] {
        var effects: [String] = []
        switch preferences.brandPreference {
        case .ownBrandPreferred: effects.append("Own-brand preference applied")
        case .brandedPreferred: effects.append("Branded preference applied")
        case .brandedOnly: effects.append("Branded-only filter applied")
        case .neutral: break
        }
        if preferences.avoidPremium { effects.append("Premium products excluded") }
        if preferences.organicOnly { effects.append("Organic-only filter applied") }
        if let maxSupermarkets { effects.append("Limited to \(maxSupermarkets) store\(maxSupermarkets == 1 ? "" : "s")") }
        return effects
    }

    private func constrainSelections(_ selections: [ItemSelectionResult], maxSupermarkets: Int?) -> [ItemSelectionResult] {
        guard let maxSupermarkets, maxSupermarkets > 0 else { return selections }
        var allowed: Set<String> = []
        var constrained: [ItemSelectionResult] = []
        for selection in selections.sorted(by: { $0.totalPrice < $1.totalPrice }) {
            if allowed.contains(selection.supermarket.name) || allowed.count < maxSupermarkets {
                allowed.insert(selection.supermarket.name)
                constrained.append(selection)
            }
        }
        return constrained
    }

    private func resolveIntent(item: ShoppingItem) -> GroceryIntent {
        let normalized = item.name.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let catalogItem = groceryCatalogService.catalogItem(matching: normalized)

        let category: GroceryCategory
        switch (catalogItem?.genericName.lowercased() ?? normalized) {
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

        return GroceryIntent(userInput: catalogItem?.displayName ?? item.name, category: category, quantity: item.quantity)
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
                    matchType: best.matchType,
                    matchExplanation: best.matchExplanation,
                    selectionReason: best.selectionReason,
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
        var score = Decimal(0.0)
        var reasons: [String] = []

        if product.category == intent.category {
            quality = .exact
            score += 0.18
            reasons.append("Exact category match for \(intent.category.displayName.lowercased()).")
        }

        let searchableText = ([product.name, product.subcategory, product.category.rawValue] + product.tags).joined(separator: " ").lowercased()
        let intentTokens = expandedTokens(from: intent.acceptedKeywords + [intent.userInput])
        let productTokens = expandedTokens(from: [searchableText])
        let tokenHits = Array(intentTokens.intersection(productTokens)).sorted()

        if !tokenHits.isEmpty {
            score += Decimal(min(tokenHits.count, 5)) * 0.07
            reasons.append("Matched tokens: \(tokenHits.prefix(4).joined(separator: ", ")).")
            if quality == .weakSubstitute {
                quality = .acceptableEquivalent
            }
        }

        let nameScore = Decimal(string: String(format: "%.3f", similarity(intent.normalizedInput, product.name.lowercased()))) ?? 0
        score += nameScore * 0.32
        reasons.append("Name similarity score: \(nameScore).")

        let sizeScore = sizeSimilarity(intent: intent.normalizedInput, candidateSize: product.size)
        score += sizeScore * 0.22
        if sizeScore <= 0.1 {
            reasons.append("Large size mismatch detected.")
            if quality == .exact { quality = .acceptableEquivalent }
        } else if sizeScore < 1 {
            reasons.append("Near size range match accepted.")
        } else {
            reasons.append("Requested size range matched.")
        }

        switch preferences.brandPreference {
        case .ownBrandPreferred:
            if product.isOwnBrand {
                score += 0.10
                reasons.append("Own-brand preference matched.")
            } else {
                score -= 0.10
            }
        case .brandedPreferred:
            if !product.isOwnBrand {
                score += 0.10
                reasons.append("Branded preference matched.")
            } else {
                score -= 0.10
            }
        case .brandedOnly:
            if product.isOwnBrand {
                reasons.append("Rejected by branded-only preference.")
                return nil
            }
            score += 0.07
            reasons.append("Branded-only preference applied.")
        case .neutral:
            break
        }

        if preferences.avoidPremium && product.isPremium {
            score -= 0.20
            reasons.append("Price sanity penalty: premium item deprioritised.")
            if quality == .exact {
                quality = .acceptableEquivalent
            }
        }

        if product.isOrganic {
            score += 0.03
            reasons.append("Organic option available.")
        }
        if product.price > 25 {
            score -= 0.08
            reasons.append("Price sanity check reduced confidence for unusually high price.")
        }

        if product.price <= 0 || product.unitValue <= 0 { return nil }

        let weightedUnit = max(Decimal(0.0001), product.unitValue - (score * 0.02))
        let finalScore = max(0.10, min(0.99, score))
        if tokenHits.isEmpty && intent.category == .unknown {
            reasons.append("Rejected as weak unknown-category match.")
            return nil
        }
        if finalScore < 0.22 {
            reasons.append("Rejected due to low confidence score \(finalScore).")
            return nil
        }
        reasons.append("Compared using weighted name/category/size/brand/price checks.")

        let matchType: ProductMatchType = finalScore >= 0.85 && quality == .exact ? .exact : (finalScore >= 0.60 ? .close : .approximate)

        return ProductCandidate(
            id: UUID(),
            intent: intent,
            supermarket: supermarket,
            product: product,
            matchQuality: quality,
            confidence: finalScore,
            weightedUnitValue: weightedUnit,
            isValid: true,
            matchType: matchType,
            matchExplanation: reasons.first ?? "Chosen as strongest available candidate.",
            selectionReason: "Selected as top-ranked option from scored candidates.",
            reasons: reasons
        )
    }

    private func similarity(_ lhs: String, _ rhs: String) -> Double {
        let left = Set(lhs.split(whereSeparator: { !$0.isLetter && !$0.isNumber }).map(String.init))
        let right = Set(rhs.split(whereSeparator: { !$0.isLetter && !$0.isNumber }).map(String.init))
        guard !left.isEmpty || !right.isEmpty else { return 0 }
        let overlap = left.intersection(right).count
        return Double(overlap) / Double(max(left.count, right.count))
    }

    private func sizeSimilarity(intent: String, candidateSize: String) -> Decimal {
        func parse(_ text: String) -> (Double, String)? {
            let lower = text.lowercased().replacingOccurrences(of: " ", with: "")
            for unit in ["kg", "g", "ml", "l"] {
                guard let range = lower.range(of: unit) else { continue }
                let prefix = lower[..<range.lowerBound]
                let numeric = prefix.filter { $0.isNumber || $0 == "." }
                if let value = Double(numeric) {
                    return (value, unit)
                }
            }
            return nil
        }
        guard
            let requested = parse(intent),
            let candidate = parse(candidateSize),
            requested.1 == candidate.1,
            requested.0 > 0
        else { return 0.35 }
        let ratio = candidate.0 / requested.0
        if ratio >= 0.9 && ratio <= 1.1 { return 1.0 }
        if ratio >= 0.7 && ratio <= 1.3 { return 0.7 }
        return 0.1
    }

    private func expandedTokens(from values: [String]) -> Set<String> {
        let synonyms: [String: [String]] = [
            "beanz": ["beans", "baked"],
            "yoghurt": ["yogurt"],
            "loaf": ["bread"],
            "fillets": ["fillet", "breast"]
        ]

        var tokens = Set<String>()
        for value in values {
            for raw in value.lowercased().split(whereSeparator: { !$0.isLetter && !$0.isNumber }) {
                var token = String(raw)
                if token.count > 3 && token.hasSuffix("ies") {
                    token = String(token.dropLast(3)) + "y"
                } else if token.count > 3 && token.hasSuffix("es") {
                    token = String(token.dropLast(2))
                } else if token.count > 2 && token.hasSuffix("s") {
                    token = String(token.dropLast())
                }
                tokens.insert(token)
                for synonym in synonyms[token, default: []] {
                    tokens.insert(synonym)
                }
            }
        }
        return tokens
    }

}
