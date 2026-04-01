import Foundation
import Combine

final class SavedListsViewModel: ObservableObject {
    @Published private(set) var savedLists: [ShoppingList] = []
    private let store: ShoppingListStore

    init(store: ShoppingListStore) {
        self.store = store
        self.savedLists = store.savedLists
        store.$savedLists
            .receive(on: DispatchQueue.main)
            .assign(to: &$savedLists)
    }

    func delete(at offsets: IndexSet) {
        store.delete(indexSet: offsets)
    }

    func duplicate(_ list: ShoppingList) {
        store.duplicate(listID: list.id)
    }

    func update(_ list: ShoppingList) {
        store.update(list: list)
    }

    func rerun(_ list: ShoppingList) {
        store.markCompared(listID: list.id)
    }
}
