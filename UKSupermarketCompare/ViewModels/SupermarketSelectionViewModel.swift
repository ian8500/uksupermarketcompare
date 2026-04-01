import Foundation

final class SupermarketSelectionViewModel: ObservableObject {
    @Published var selectedMarketIDs: Set<UUID> = []
    @Published var comparisonMode: BasketComparisonMode = .cheapestPossible
    @Published var brandPreference: BrandPreference = .neutral
    @Published var avoidPremium: Bool = false
    @Published var organicOnly: Bool = false
    @Published var maxStores: Int = 0

    let shoppingList: ShoppingList
    let supermarkets: [Supermarket]
    private let coordinator: AppCoordinatorViewModel

    init(shoppingList: ShoppingList, coordinator: AppCoordinatorViewModel) {
        self.shoppingList = shoppingList
        self.coordinator = coordinator
        self.supermarkets = coordinator.supermarkets()
        self.selectedMarketIDs = Set(supermarkets.prefix(3).map(\.id))
    }

    var canCompare: Bool {
        !selectedMarketIDs.isEmpty
    }

    var basketPreferences: BasketUserPreferences {
        BasketUserPreferences(
            brandPreference: brandPreference,
            avoidPremium: avoidPremium,
            organicOnly: organicOnly
        )
    }

    var maxSupermarkets: Int? {
        maxStores == 0 ? nil : maxStores
    }

    func toggleSelection(for supermarket: Supermarket) {
        if selectedMarketIDs.contains(supermarket.id) {
            selectedMarketIDs.remove(supermarket.id)
        } else {
            selectedMarketIDs.insert(supermarket.id)
        }
    }

    func runComparison() {
        let markets = supermarkets.filter { selectedMarketIDs.contains($0.id) }
        coordinator.store.markCompared(listID: shoppingList.id)
        let result = coordinator.compare(
            list: shoppingList,
            markets: markets,
            mode: comparisonMode,
            preferences: basketPreferences,
            maxSupermarkets: maxSupermarkets
        )
        coordinator.openResults(result)
    }
}
