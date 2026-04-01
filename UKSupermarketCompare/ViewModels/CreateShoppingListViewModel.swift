import Foundation

final class CreateShoppingListViewModel: ObservableObject {
    @Published var listTitle = "Weekly Shop"
    @Published var itemName = "" {
        didSet { refreshSuggestions() }
    }
    @Published var quantity = 1
    @Published private(set) var items: [ShoppingItem] = []
    @Published private(set) var suggestions: [GrocerySuggestion] = []

    let weeklyEssentials = ["Milk", "Bread", "Eggs", "Butter", "Bananas", "Rice"]

    private let coordinator: AppCoordinatorViewModel
    private let catalogService: GroceryCatalogServing

    init(coordinator: AppCoordinatorViewModel, catalogService: GroceryCatalogServing) {
        self.coordinator = coordinator
        self.catalogService = catalogService
        self.suggestions = catalogService.suggestions(for: "", limit: 6)
    }

    var canAddItem: Bool {
        !itemName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var canContinue: Bool {
        !items.isEmpty && !listTitle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var recentItems: [String] {
        coordinator.store.recentItems
    }

    func applySuggestion(_ suggestion: GrocerySuggestion) {
        itemName = suggestion.item.displayName
        quantity = max(1, suggestion.item.defaultQuantityStep)
    }

    func addItem() {
        guard canAddItem else { return }
        let parsed = parseQuantityPrefix(from: itemName)
        let cleanedName = parsed.name
        let resolvedName = catalogService.catalogItem(matching: cleanedName)?.displayName ?? cleanedName.capitalized
        let resolvedQuantity = parsed.quantity ?? quantity
        items.append(ShoppingItem(name: resolvedName, quantity: max(resolvedQuantity, 1)))
        itemName = ""
        quantity = 1
        refreshSuggestions()
        print("[Analytics] item_added name=\(resolvedName) qty=\(resolvedQuantity)")
    }

    func addRecentItem(_ name: String) {
        itemName = name
        quantity = 1
        addItem()
    }

    func quickAddEssential(_ name: String) {
        itemName = name
        quantity = 1
        addItem()
    }

    func quickAddSuggestion(_ suggestion: GrocerySuggestion) {
        applySuggestion(suggestion)
        addItem()
    }

    func updateQuantity(for itemID: UUID, delta: Int) {
        guard let index = items.firstIndex(where: { $0.id == itemID }) else { return }
        items[index].quantity = max(1, items[index].quantity + delta)
    }

    func deleteItem(at offsets: IndexSet) {
        items.remove(atOffsets: offsets)
    }

    func continueToSupermarketSelection() {
        guard canContinue else { return }
        let list = ShoppingList(title: listTitle.trimmingCharacters(in: .whitespacesAndNewlines), items: items)
        coordinator.store.rememberItems(from: items)
        coordinator.openSelection(for: list)
        print("[Analytics] basket_started items=\(items.count)")
    }

    private func refreshSuggestions() {
        suggestions = catalogService.suggestions(for: parseQuantityPrefix(from: itemName).name, limit: 8)
    }

    private func parseQuantityPrefix(from raw: String) -> (name: String, quantity: Int?) {
        let cleaned = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        let tokens = cleaned.split(separator: " ", omittingEmptySubsequences: true)
        guard let first = tokens.first, let parsedQty = Int(first), parsedQty > 0 else {
            return (cleaned, nil)
        }

        let remainder = tokens.dropFirst().joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
        guard !remainder.isEmpty else { return (cleaned, nil) }
        return (remainder, min(parsedQty, 99))
    }
}
