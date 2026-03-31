import Foundation

final class BasketComparisonResultsViewModel: ObservableObject {
    let result: BasketComparisonResult
    private let store: ShoppingListStore

    init(result: BasketComparisonResult, store: ShoppingListStore) {
        self.result = result
        self.store = store
    }

    func saveList() {
        store.save(list: result.shoppingList)
    }
}
