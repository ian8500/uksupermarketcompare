import Foundation

final class ShoppingListStore: ObservableObject {
    @Published private(set) var savedLists: [ShoppingList] = []

    private let defaults: UserDefaults
    private let storageKey = "saved_shopping_lists"

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        load()
    }

    func save(list: ShoppingList) {
        savedLists.removeAll { $0.id == list.id }
        savedLists.insert(list, at: 0)
        persist()
    }

    func delete(indexSet: IndexSet) {
        savedLists.remove(atOffsets: indexSet)
        persist()
    }

    private func load() {
        guard let data = defaults.data(forKey: storageKey) else {
            return
        }

        do {
            savedLists = try JSONDecoder().decode([ShoppingList].self, from: data)
        } catch {
            savedLists = []
        }
    }

    private func persist() {
        do {
            let data = try JSONEncoder().encode(savedLists)
            defaults.set(data, forKey: storageKey)
        } catch {
            assertionFailure("Unable to persist shopping lists: \(error.localizedDescription)")
        }
    }
}
