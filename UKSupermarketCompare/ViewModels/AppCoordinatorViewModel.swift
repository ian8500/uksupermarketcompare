import Foundation

final class AppCoordinatorViewModel: ObservableObject {
    @Published var path: [AppRoute] = []
    @Published var dataSourceStatus: AppDataSourceStatus

    let store: ShoppingListStore
    let groceryCatalogService: GroceryCatalogServing
    private let dataProvider: SupermarketDataProviding
    private let basketService: BasketOptimising

    init(
        store: ShoppingListStore = ShoppingListStore(),
        dataProvider: SupermarketDataProviding? = nil,
        groceryCatalogService: GroceryCatalogServing = GroceryCatalogService(),
        basketService: BasketOptimising? = nil
    ) {
        self.store = store
        self.groceryCatalogService = groceryCatalogService

        if let dataProvider {
            print("[AppCoordinator] Using injected data provider: \(type(of: dataProvider))")
            self.dataProvider = dataProvider
            let count = dataProvider.supermarkets().count
            self.dataSourceStatus = AppDataSourceStatus.mock(liveURL: nil, supermarketCount: count)
        } else if let config = LiveSupermarketDataService.Config.fromEnvironment() {
            print("[AppCoordinator] LIVE source configured at \(config.url.absoluteString)")
            let liveProvider = LiveSupermarketDataService(config: config)
            if liveProvider.diagnostics.wasSuccessful {
                print("[AppCoordinator] LIVE source active with \(liveProvider.diagnostics.supermarketCount) supermarkets.")
                self.dataProvider = liveProvider
                self.dataSourceStatus = AppDataSourceStatus(
                    mode: .live,
                    liveURL: config.url,
                    lastLiveLoadError: nil,
                    supermarketCount: liveProvider.diagnostics.supermarketCount,
                    lastLoadAt: liveProvider.diagnostics.completedAt,
                    backendMarker: liveProvider.diagnostics.backendMarker
                )
            } else {
                print("[AppCoordinator] LIVE source failed, falling back to MOCK. error=\(liveProvider.diagnostics.errorDescription ?? "unknown")")
                let mock = MockSupermarketDataService()
                self.dataProvider = mock
                self.dataSourceStatus = AppDataSourceStatus.mock(
                    liveURL: config.url,
                    error: liveProvider.diagnostics.errorDescription,
                    marker: liveProvider.diagnostics.backendMarker,
                    supermarketCount: mock.supermarkets().count
                )
            }
        } else {
            let mock = MockSupermarketDataService()
            print("[AppCoordinator] LIVE source not configured; using MOCK data.")
            self.dataProvider = mock
            self.dataSourceStatus = AppDataSourceStatus.mock(liveURL: nil, supermarketCount: mock.supermarkets().count)
        }

        self.basketService = basketService ?? BasketOptimiserService(dataProvider: self.dataProvider, groceryCatalogService: groceryCatalogService)
    }

    func supermarkets() -> [Supermarket] {
        dataProvider.supermarkets()
    }

    func compare(
        list: ShoppingList,
        markets: [Supermarket],
        mode: BasketComparisonMode,
        preferences: BasketUserPreferences,
        maxSupermarkets: Int?
    ) -> BasketOptimisationResult {
        basketService.optimise(
            shoppingList: list,
            supermarkets: markets,
            mode: mode,
            preferences: preferences,
            maxSupermarkets: maxSupermarkets
        )
    }

    func openCreateList() { path.append(.createList) }
    func openSavedLists() { path.append(.savedLists) }
    func openSelection(for list: ShoppingList) { path.append(.supermarketSelection(list)) }
    func openResults(_ result: BasketOptimisationResult) { path.append(.comparison(result)) }
    func openSavedListDetail(_ list: ShoppingList) { path.append(.savedListDetail(list)) }
}
