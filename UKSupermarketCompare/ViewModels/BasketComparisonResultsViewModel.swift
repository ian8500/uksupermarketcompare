import Foundation

final class BasketComparisonResultsViewModel: ObservableObject {
    let result: BasketOptimisationResult
    private let store: ShoppingListStore

    init(result: BasketOptimisationResult, store: ShoppingListStore) {
        self.result = result
        self.store = store
    }

    func saveList() {
        store.save(list: result.shoppingList)
    }
}
