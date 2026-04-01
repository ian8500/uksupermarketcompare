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
        "You save \(result.savingsVsMostExpensive, format: .currency(code: "GBP")) vs the priciest option and \(result.savingsVsCheapestSingleStore, format: .currency(code: "GBP")) vs the best single-store basket."
    }

    func saveList() {
        store.save(list: result.shoppingList)
        print("[Analytics] basket_saved items=\(result.shoppingList.items.count)")
    }
}
