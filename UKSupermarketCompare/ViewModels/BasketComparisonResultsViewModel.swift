import Foundation

final class BasketComparisonResultsViewModel: ObservableObject {
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

    var savingsExplanation: String {
        "You save \(result.savingsVsMostExpensive.asGBP()) vs the priciest option and \(result.savingsVsCheapestSingleStore.asGBP()) vs the best single-store basket."
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

    var purchasePlanByStore: [(supermarket: Supermarket, selections: [ItemSelectionResult], total: Decimal)] {
        let grouped = Dictionary(grouping: result.selectedBasket.selections, by: \.supermarket)
        return grouped
            .map { supermarket, selections in
                let sortedSelections = selections.sorted { $0.intent.userInput.localizedCaseInsensitiveCompare($1.intent.userInput) == .orderedAscending }
                let total = sortedSelections.reduce(Decimal.zero) { $0 + $1.totalPrice }
                return (supermarket: supermarket, selections: sortedSelections, total: total)
            }
            .sorted { $0.total < $1.total }
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

    func saveList() {
        store.save(list: result.shoppingList)
        print("[Analytics] basket_saved items=\(result.shoppingList.items.count)")
    }
}
