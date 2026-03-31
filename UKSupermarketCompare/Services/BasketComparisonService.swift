import Foundation

protocol BasketOptimising {
    func optimise(shoppingList: ShoppingList, supermarkets: [Supermarket]) -> BasketOptimisationResult
}

final class BasketOptimiserService: BasketOptimising {
    private let dataProvider: SupermarketDataProviding

    init(dataProvider: SupermarketDataProviding) {
        self.dataProvider = dataProvider
    }

    func optimise(shoppingList: ShoppingList, supermarkets: [Supermarket]) -> BasketOptimisationResult {
        let intents = shoppingList.items.map(resolveIntent)
        let totals = supermarkets.map { buildSupermarketTotal(for: $0, intents: intents) }
            .sorted { $0.total < $1.total }

        let mixedSelections: [ItemSelectionResult] = intents.compactMap { intent in
            let options = totals.compactMap { total in
                total.selections.first(where: { $0.intent.id == intent.id })
            }
            return options.min { lhs, rhs in
                if lhs.totalPrice == rhs.totalPrice {
                    return lhs.matchQuality > rhs.matchQuality
                }
                return lhs.totalPrice < rhs.totalPrice
            }
        }

        let unavailable = intents.filter { intent in
            !mixedSelections.contains(where: { $0.intent.id == intent.id })
        }

        let mixed = MixedBasketResult(selections: mixedSelections, unavailableItems: unavailable)
        let cheapestSingle = totals.first(where: { $0.unavailableItems.isEmpty })

        return BasketOptimisationResult(
            shoppingList: shoppingList,
            intents: intents,
            supermarketTotals: totals,
            cheapestSingleStore: cheapestSingle,
            mixedBasket: mixed
        )
    }

    private func resolveIntent(item: ShoppingItem) -> GroceryIntent {
        let normalized = item.name.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let category: GroceryCategory

        switch normalized {
        case let value where value.contains("milk"): category = .milk
        case let value where value.contains("bread"): category = .bread
        case let value where value.contains("egg"): category = .eggs
        case let value where value.contains("butter") || value.contains("spread"): category = .butter
        case let value where value.contains("pasta") || value.contains("spaghetti") || value.contains("penne"): category = .pasta
        case let value where value.contains("bean"): category = .bakedBeans
        case let value where value.contains("banana"): category = .bananas
        case let value where value.contains("chicken"): category = .chickenBreast
        case let value where value.contains("cereal") || value.contains("flakes") || value.contains("muesli"): category = .cereal
        case let value where value.contains("cheese") || value.contains("cheddar"): category = .cheese
        default: category = .unknown
        }

        return GroceryIntent(userInput: item.name, category: category, quantity: item.quantity)
    }

    private func buildSupermarketTotal(for supermarket: Supermarket, intents: [GroceryIntent]) -> SupermarketBasketTotal {
        let products = dataProvider.products(at: supermarket)
        var selections: [ItemSelectionResult] = []
        var unavailable: [GroceryIntent] = []

        for intent in intents {
            let candidates = products.compactMap { candidate(for: intent, supermarket: supermarket, product: $0) }
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
                    confidence: best.confidence
                )
            )
        }

        return SupermarketBasketTotal(supermarket: supermarket, selections: selections, unavailableItems: unavailable)
    }

    private func candidateSort(lhs: ProductCandidate, rhs: ProductCandidate) -> Bool {
        if lhs.matchQuality != rhs.matchQuality {
            return lhs.matchQuality > rhs.matchQuality
        }
        if lhs.product.isPremium != rhs.product.isPremium {
            return rhs.product.isPremium
        }
        if lhs.product.price != rhs.product.price {
            return lhs.product.price < rhs.product.price
        }
        return lhs.confidence > rhs.confidence
    }

    private func candidate(for intent: GroceryIntent, supermarket: Supermarket, product: SupermarketProduct) -> ProductCandidate? {
        var quality: MatchQuality?
        var score = Decimal.zero
        var valid = true

        if intent.category != .unknown {
            guard product.category == intent.category else { return nil }
        }

        if product.category == intent.category {
            quality = .exact
            score += 0.55
        } else if intent.acceptedKeywords.contains(where: { product.tags.contains($0) || product.name.lowercased().contains($0) }) {
            quality = .acceptableEquivalent
            score += 0.35
        }

        if product.isPremium {
            score -= 0.20
            if quality == .exact { quality = .acceptableEquivalent }
        }

        if product.subcategory.contains("spreadable") && intent.category == .butter {
            quality = min(quality ?? .weakSubstitute, .weakSubstitute)
            score -= 0.10
        }

        if intent.category == .cheese && !product.subcategory.contains("cheddar") {
            quality = .weakSubstitute
            score -= 0.15
        }

        if product.price <= 0 {
            valid = false
        }

        guard let matchQuality = quality else { return nil }
        let finalScore = max(0.10, min(0.99, score + 0.40))

        return ProductCandidate(
            id: UUID(),
            intent: intent,
            supermarket: supermarket,
            product: product,
            matchQuality: matchQuality,
            confidence: finalScore,
            isValid: valid
        )
    }
}
