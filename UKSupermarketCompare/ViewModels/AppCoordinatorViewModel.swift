import Foundation

final class AppCoordinatorViewModel: ObservableObject {
    @Published var path: [AppRoute] = []

    let store: ShoppingListStore
    let groceryCatalogService: GroceryCatalogServing
    private let dataProvider: SupermarketDataProviding
    private let basketService: BasketOptimising

    init(
        store: ShoppingListStore = ShoppingListStore(),
        dataProvider: SupermarketDataProviding = MockSupermarketDataService(),
        groceryCatalogService: GroceryCatalogServing = GroceryCatalogService(),
        basketService: BasketOptimising? = nil
    ) {
        self.store = store
        self.dataProvider = dataProvider
        self.groceryCatalogService = groceryCatalogService
        self.basketService = basketService ?? BasketOptimiserService(dataProvider: dataProvider, groceryCatalogService: groceryCatalogService)
    }

    func supermarkets() -> [Supermarket] {
        dataProvider.supermarkets()
    }

    func compare(
        list: ShoppingList,
        markets: [Supermarket],
        mode: BasketComparisonMode,
        preferences: BasketUserPreferences
    ) -> BasketOptimisationResult {
        basketService.optimise(shoppingList: list, supermarkets: markets, mode: mode, preferences: preferences)
    }

    func openCreateList() { path.append(.createList) }
    func openSavedLists() { path.append(.savedLists) }
    func openSelection(for list: ShoppingList) { path.append(.supermarketSelection(list)) }
    func openResults(_ result: BasketOptimisationResult) { path.append(.comparison(result)) }
    func openSavedListDetail(_ list: ShoppingList) { path.append(.savedListDetail(list)) }
}
