import Foundation

final class CreateShoppingListViewModel: ObservableObject {
    @Published var listTitle = "Weekly Shop"
    @Published var itemName = "" {
        didSet { refreshSuggestions() }
    }
    @Published var quantity = 1
    @Published private(set) var items: [ShoppingItem] = []
    @Published private(set) var suggestions: [GrocerySuggestion] = []

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

    func applySuggestion(_ suggestion: GrocerySuggestion) {
        itemName = suggestion.item.displayName
        quantity = max(1, suggestion.item.defaultQuantityStep)
    }

    func addItem() {
        guard canAddItem else { return }
        let cleanedName = itemName.trimmingCharacters(in: .whitespacesAndNewlines)
        let resolvedName = catalogService.catalogItem(matching: cleanedName)?.displayName ?? cleanedName.capitalized
        items.append(ShoppingItem(name: resolvedName, quantity: max(quantity, 1)))
        itemName = ""
        quantity = 1
        refreshSuggestions()
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
        coordinator.openSelection(for: list)
    }

    private func refreshSuggestions() {
        suggestions = catalogService.suggestions(for: itemName, limit: 8)
    }
}
