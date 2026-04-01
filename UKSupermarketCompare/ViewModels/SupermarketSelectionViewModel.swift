import Foundation

@MainActor
final class SupermarketSelectionViewModel: ObservableObject {
    struct ModeOption: Identifiable {
        let mode: BasketComparisonMode
        var id: BasketComparisonMode { mode }
    }

    @Published var selectedMarketIDs: Set<UUID> = []
    @Published var comparisonMode: BasketComparisonMode = .cheapestPossible
    @Published var brandPreference: BrandPreference = .neutral
    @Published var avoidPremium: Bool = false
    @Published var organicOnly: Bool = false
    @Published var maxStores: Int = 0
    @Published var isComparing: Bool = false
    @Published var comparePhase = "Ready to compare"

    let shoppingList: ShoppingList
    let supermarkets: [Supermarket]
    private let coordinator: AppCoordinatorViewModel
    private let basketCache = BasketComparisonCache.shared

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

    var modeOptions: [ModeOption] {
        BasketComparisonMode.allCases.map { ModeOption(mode: $0) }
    }

    var selectedModeSummary: String {
        comparisonMode.summary
    }

    func toggleSelection(for supermarket: Supermarket) {
        if selectedMarketIDs.contains(supermarket.id) {
            selectedMarketIDs.remove(supermarket.id)
        } else {
            selectedMarketIDs.insert(supermarket.id)
        }
    }

    func runComparison() {
        guard !isComparing else { return }
        isComparing = true
        comparePhase = "Preparing basket..."
        HapticFeedbackService.compareBasket()

        Task {
            let markets = supermarkets.filter { selectedMarketIDs.contains($0.id) }
            let cacheKey = makeCacheKey(markets: markets)

            if let cached = await basketCache.result(for: cacheKey) {
                coordinator.store.markCompared(listID: shoppingList.id)
                comparePhase = "Loaded instantly"
                isComparing = false
                coordinator.openResults(cached)
                return
            }

            comparePhase = "Finding best prices..."
            let result = await coordinator.compareAsync(
                list: shoppingList,
                markets: markets,
                mode: comparisonMode,
                preferences: basketPreferences,
                maxSupermarkets: maxSupermarkets
            )

            await basketCache.store(result, for: cacheKey)
            coordinator.store.markCompared(listID: shoppingList.id)
            comparePhase = "Building your action plan..."
            isComparing = false
            coordinator.openResults(result)
        }
    }

    private func makeCacheKey(markets: [Supermarket]) -> String {
        let sortedMarkets = markets.map(\.name).sorted().joined(separator: "|")
        let items = shoppingList.items.map { "\($0.name.lowercased())x\($0.quantity)" }.sorted().joined(separator: "|")
        return [
            sortedMarkets,
            items,
            comparisonMode.rawValue,
            brandPreference.rawValue,
            avoidPremium.description,
            organicOnly.description,
            String(maxStores)
        ].joined(separator: "#")
    }
}
