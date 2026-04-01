import Foundation

final class BasketComparisonResultsViewModel: ObservableObject {
    struct StrategyCard: Identifiable {
        let title: String
        let total: Decimal
        let storesUsed: [String]
        let savingsHeadline: String
        let explanation: String
        let isSelected: Bool
        let tint: String

        var id: String { title }
    }

    struct PurchasePlanStoreGroup: Identifiable {
        let supermarket: Supermarket
        let selections: [ItemSelectionResult]
        let subtotal: Decimal

        var id: UUID { supermarket.id }
        var itemCount: Int { selections.reduce(0) { $0 + $1.quantity } }
    }

    let result: BasketOptimisationResult
    private let store: ShoppingListStore

    init(result: BasketOptimisationResult, store: ShoppingListStore) {
        self.result = result
        self.store = store
    }

    var bestConvenienceOption: SupermarketBasketTotal? {
        result.supermarketTotals.min {
            let lhsScore = $0.total + Decimal($0.unavailableItems.count * 5)
            let rhsScore = $1.total + Decimal($1.unavailableItems.count * 5)
            return lhsScore < rhsScore
        }
    }

    var preferenceEffects: [String] {
        result.preferenceEffects ?? []
    }

    var selectedStoresUsed: [String] {
        Array(Set(result.selectedBasket.selections.map { $0.supermarket.name })).sorted()
    }

    var mixedBasketSavingsVsSingleStore: Decimal {
        guard let cheapestSingle = result.cheapestSingleStore else { return .zero }
        return cheapestSingle.total - result.mixedBasket.total
    }

    var convenienceSavingsVsHighest: Decimal {
        guard let convenience = bestConvenienceOption else { return .zero }
        guard let mostExpensive = result.mostExpensiveCompleteStoreTotal else { return .zero }
        return mostExpensive - convenience.total
    }

    var purchasePlanByStore: [PurchasePlanStoreGroup] {
        let grouped = Dictionary(grouping: result.selectedBasket.selections, by: \.supermarket)
        return grouped
            .map { supermarket, selections in
                let sortedSelections = selections.sorted { $0.intent.userInput.localizedCaseInsensitiveCompare($1.intent.userInput) == .orderedAscending }
                let total = sortedSelections.reduce(Decimal.zero) { $0 + $1.totalPrice }
                return PurchasePlanStoreGroup(supermarket: supermarket, selections: sortedSelections, subtotal: total)
            }
            .sorted { $0.subtotal < $1.subtotal }
    }

    var purchasePlanOverallTotal: Decimal {
        purchasePlanByStore.reduce(Decimal.zero) { $0 + $1.subtotal }
    }

    var selectedStrategyReason: String {
        switch result.comparisonMode {
        case .cheapestPossible:
            return "We chose the lowest overall basket total using the supermarkets you selected."
        case .cheapestSingleStoreOnly:
            return "We chose the strongest one-store basket so you can check out in one trip."
        case .bestConvenienceOption:
            return "We prioritised a practical one-store checkout while keeping total cost competitive."
        }
    }

    var strategyTradeOffSummary: String {
        guard let cheapestSingle = result.cheapestSingleStore else {
            return "No fully matched single-store basket was available, so this strategy prioritised completion and value."
        }

        let delta = (result.selectedBasket.total - cheapestSingle.total)
        if delta < .zero {
            return "Compared with the best single-store basket, this plan saves an extra \((-delta).asGBP())."
        } else if delta > .zero {
            return "Compared with the best single-store basket, this plan costs \(delta.asGBP()) more for your selected strategy."
        }
        return "This matches the best single-store total while following your chosen strategy."
    }

    var convenienceVsSavingsSummary: String {
        let stores = max(selectedStoresUsed.count, 1)
        if stores == 1 {
            return "You only need one store, so convenience is high without extra travel time."
        }

        let delta = result.savingsVsCheapestSingleStore
        if delta > .zero {
            return "This plan uses \(stores) stores to save \(delta.asGBP()) versus the best one-store checkout."
        } else if delta < .zero {
            return "This plan uses \(stores) stores and adds \((-delta).asGBP()) versus the best one-store checkout."
        }
        return "This plan uses \(stores) stores and lands at the same price as the best one-store checkout."
    }

    var selectedModeTitle: String {
        result.comparisonMode.title
    }

    var selectedModeSummary: String {
        result.comparisonMode.summary
    }

    var strategyCards: [StrategyCard] {
        var cards: [StrategyCard] = []

        if let cheapestSingle = result.cheapestSingleStore {
            cards.append(
                StrategyCard(
                    title: "Cheapest Single-Store",
                    total: cheapestSingle.total,
                    storesUsed: [cheapestSingle.supermarket.name],
                    savingsHeadline: "Reference for one-trip checkout",
                    explanation: "Best one-shop checkout with zero switching between supermarkets.",
                    isSelected: result.comparisonMode == .cheapestSingleStoreOnly,
                    tint: "blue"
                )
            )
        }

        cards.append(
            StrategyCard(
                title: "Cheapest Mixed Basket",
                total: result.mixedBasket.total,
                storesUsed: result.mixedBasket.supermarketsUsed,
                savingsHeadline: mixedBasketSavingsVsSingleStore > 0
                    ? "Saves \(mixedBasketSavingsVsSingleStore.asGBP()) vs best single-store"
                    : "Best raw price across selected stores",
                explanation: "Lowest total cost by combining strongest prices across supermarkets.",
                isSelected: result.comparisonMode == .cheapestPossible,
                tint: "green"
            )
        )

        if let convenience = bestConvenienceOption {
            cards.append(
                StrategyCard(
                    title: "Best Convenience Option",
                    total: convenience.total,
                    storesUsed: [convenience.supermarket.name],
                    savingsHeadline: convenience.unavailableItems.isEmpty
                        ? "Complete one-store basket"
                        : "\(convenience.unavailableItems.count) missing item(s) possible",
                    explanation: "Simple near-complete trip with strong value and fewer handoffs.",
                    isSelected: result.comparisonMode == .bestConvenienceOption,
                    tint: "navy"
                )
            )
        }
        return cards
    }

    var missingItemsSummary: String {
        let missing = result.selectedBasket.unavailableItems.count
        guard missing > 0 else {
            return "Everything in your basket was matched with confident options."
        }
        return "\(missing) item(s) were not confidently matched. Try broader names or add another supermarket for fuller coverage."
    }

    var savingsStory: String {
        let expensive = result.savingsVsMostExpensive
        let singleStore = result.savingsVsCheapestSingleStore
        let conveniencePremium = max(result.selectedBasket.total - (result.cheapestSingleStore?.total ?? result.selectedBasket.total), .zero)
        let stores = max(selectedStoresUsed.count, 1)

        return "You save \(expensive.asGBP()) vs the most expensive complete option, \(singleStore.asGBP()) vs the cheapest single-store basket, with \(stores) store(s) in this plan and \(conveniencePremium.asGBP()) extra for convenience mode where applicable."
    }

    func alternatives(for intent: GroceryIntent, limit: Int = 2) -> [ItemSelectionResult] {
        let candidates = result.supermarketTotals
            .flatMap(\.selections)
            .filter { $0.intent.category == intent.category }
            .sorted { $0.totalPrice < $1.totalPrice }

        var seenStores = Set<UUID>()
        var unique: [ItemSelectionResult] = []
        for candidate in candidates where !seenStores.contains(candidate.supermarket.id) {
            seenStores.insert(candidate.supermarket.id)
            unique.append(candidate)
            if unique.count == limit {
                break
            }
        }
        return unique
    }

    func decisionExplanation(for selection: ItemSelectionResult) -> String {
        let topReasons = Array(selection.reasons.prefix(2))
        if topReasons.isEmpty {
            return "Chosen as strongest available match."
        }
        return topReasons.joined(separator: " ")
    }

    func saveList() {
        store.save(list: result.shoppingList)
        print("[Analytics] basket_saved items=\(result.shoppingList.items.count)")
    }
}
