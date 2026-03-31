import Foundation

final class CreateShoppingListViewModel: ObservableObject {
    @Published var listTitle = "Weekly Shop"
    @Published var itemName = ""
    @Published var quantity = 1
    @Published private(set) var items: [ShoppingItem] = []

    private let coordinator: AppCoordinatorViewModel

    init(coordinator: AppCoordinatorViewModel) {
        self.coordinator = coordinator
    }

    var canAddItem: Bool {
        !itemName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var canContinue: Bool {
        !items.isEmpty && !listTitle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    func addItem() {
        guard canAddItem else { return }
        let cleanedName = itemName.trimmingCharacters(in: .whitespacesAndNewlines)
        items.append(ShoppingItem(name: cleanedName, quantity: max(quantity, 1)))
        itemName = ""
        quantity = 1
    }

    func deleteItem(at offsets: IndexSet) {
        items.remove(atOffsets: offsets)
    }

    func continueToSupermarketSelection() {
        guard canContinue else { return }
        let list = ShoppingList(title: listTitle.trimmingCharacters(in: .whitespacesAndNewlines), items: items)
        coordinator.openSelection(for: list)
    }
}
