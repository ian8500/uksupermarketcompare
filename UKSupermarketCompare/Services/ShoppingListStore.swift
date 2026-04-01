import Foundation

final class ShoppingListStore: ObservableObject {
    @Published private(set) var savedLists: [ShoppingList] = []
    @Published private(set) var recentItems: [String] = []
    @Published private(set) var favoriteItems: [String] = []
    @Published private(set) var stapleItems: [String] = []
    @Published private(set) var lastBasket: ShoppingList?

    private let defaults: UserDefaults
    private let storageKey = "saved_shopping_lists"
    private let recentItemsKey = "recent_shopping_items"
    private let favoriteItemsKey = "favorite_shopping_items"
    private let stapleItemsKey = "staple_shopping_items"
    private let lastBasketKey = "last_basket_snapshot"

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        load()
    }

    func save(list: ShoppingList) {
        savedLists.removeAll { $0.id == list.id }
        savedLists.insert(list, at: 0)
        rememberItems(from: list.items)
        updateLastBasket(list)
        persist()
    }

    func update(list: ShoppingList) {
        guard let index = savedLists.firstIndex(where: { $0.id == list.id }) else { return }
        savedLists[index] = list
        rememberItems(from: list.items)
        updateLastBasket(list)
        persist()
    }

    func markCompared(listID: UUID, comparedAt: Date = Date()) {
        guard let index = savedLists.firstIndex(where: { $0.id == listID }) else { return }
        savedLists[index].lastComparedAt = comparedAt
        persist()
    }

    func duplicate(listID: UUID) {
        guard let original = savedLists.first(where: { $0.id == listID }) else { return }
        let duplicated = ShoppingList(
            title: "\(original.title) (Copy)",
            items: original.items.map { ShoppingItem(name: $0.name, quantity: $0.quantity) }
        )
        savedLists.insert(duplicated, at: 0)
        updateLastBasket(duplicated)
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

    func toggleFavorite(itemName: String) {
        let normalized = itemName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !normalized.isEmpty else { return }
        if let index = favoriteItems.firstIndex(where: { $0.caseInsensitiveCompare(normalized) == .orderedSame }) {
            favoriteItems.remove(at: index)
        } else {
            favoriteItems.insert(normalized, at: 0)
        }
        favoriteItems = Array(favoriteItems.prefix(20))
        persist()
    }

    func isFavorite(itemName: String) -> Bool {
        favoriteItems.contains { $0.caseInsensitiveCompare(itemName) == .orderedSame }
    }

    func saveStaples(_ staples: [String]) {
        let cleaned = staples
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        stapleItems = Array(NSOrderedSet(array: cleaned)) as? [String] ?? cleaned
        stapleItems = Array(stapleItems.prefix(20))
        persist()
    }

    func updateLastBasket(_ list: ShoppingList) {
        lastBasket = ShoppingList(
            id: list.id,
            title: list.title,
            createdAt: list.createdAt,
            lastComparedAt: Date(),
            items: list.items
        )
        persist()
    }

    private func load() {
        if let data = defaults.data(forKey: storageKey), let decoded = try? JSONDecoder().decode([ShoppingList].self, from: data) {
            savedLists = decoded
        }

        if let data = defaults.data(forKey: recentItemsKey), let decoded = try? JSONDecoder().decode([String].self, from: data) {
            recentItems = decoded
        }

        if let data = defaults.data(forKey: favoriteItemsKey), let decoded = try? JSONDecoder().decode([String].self, from: data) {
            favoriteItems = decoded
        }

        if let data = defaults.data(forKey: stapleItemsKey), let decoded = try? JSONDecoder().decode([String].self, from: data) {
            stapleItems = decoded
        } else {
            stapleItems = ["Milk", "Bread", "Eggs", "Bananas", "Chicken Breast", "Pasta", "Rice", "Yogurt"]
        }

        if let data = defaults.data(forKey: lastBasketKey), let decoded = try? JSONDecoder().decode(ShoppingList.self, from: data) {
            lastBasket = decoded
        }
    }

    private func persist() {
        if let savedData = try? JSONEncoder().encode(savedLists) {
            defaults.set(savedData, forKey: storageKey)
        }

        if let recentData = try? JSONEncoder().encode(recentItems) {
            defaults.set(recentData, forKey: recentItemsKey)
        }

        if let favoriteData = try? JSONEncoder().encode(favoriteItems) {
            defaults.set(favoriteData, forKey: favoriteItemsKey)
        }

        if let stapleData = try? JSONEncoder().encode(stapleItems) {
            defaults.set(stapleData, forKey: stapleItemsKey)
        }

        if let lastBasketData = try? JSONEncoder().encode(lastBasket) {
            defaults.set(lastBasketData, forKey: lastBasketKey)
        }
    }
}
