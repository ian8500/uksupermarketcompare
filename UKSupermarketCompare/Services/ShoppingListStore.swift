import Foundation

final class ShoppingListStore: ObservableObject {
    @Published private(set) var savedLists: [ShoppingList] = []
    @Published private(set) var recentItems: [String] = []

    private let defaults: UserDefaults
    private let storageKey = "saved_shopping_lists"
    private let recentItemsKey = "recent_shopping_items"

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        load()
    }

    func save(list: ShoppingList) {
        savedLists.removeAll { $0.id == list.id }
        savedLists.insert(list, at: 0)
        rememberItems(from: list.items)
        persist()
    }

    func update(list: ShoppingList) {
        guard let index = savedLists.firstIndex(where: { $0.id == list.id }) else { return }
        savedLists[index] = list
        rememberItems(from: list.items)
        persist()
    }

    func duplicate(listID: UUID) {
        guard let original = savedLists.first(where: { $0.id == listID }) else { return }
        let duplicated = ShoppingList(
            title: "\(original.title) (Copy)",
            items: original.items.map { ShoppingItem(name: $0.name, quantity: $0.quantity) }
        )
        savedLists.insert(duplicated, at: 0)
        persist()
    }

    func delete(indexSet: IndexSet) {
        savedLists.remove(atOffsets: indexSet)
        persist()
    }

    func rememberItems(from items: [ShoppingItem]) {
        for item in items {
            let normalized = item.name.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !normalized.isEmpty else { continue }
            recentItems.removeAll { $0.caseInsensitiveCompare(normalized) == .orderedSame }
            recentItems.insert(normalized, at: 0)
        }
        recentItems = Array(recentItems.prefix(20))
        persist()
    }

    private func load() {
        if let data = defaults.data(forKey: storageKey), let decoded = try? JSONDecoder().decode([ShoppingList].self, from: data) {
            savedLists = decoded
        }

        if let data = defaults.data(forKey: recentItemsKey), let decoded = try? JSONDecoder().decode([String].self, from: data) {
            recentItems = decoded
        }
    }

    private func persist() {
        if let savedData = try? JSONEncoder().encode(savedLists) {
            defaults.set(savedData, forKey: storageKey)
        }

        if let recentData = try? JSONEncoder().encode(recentItems) {
            defaults.set(recentData, forKey: recentItemsKey)
        }
    }
}
