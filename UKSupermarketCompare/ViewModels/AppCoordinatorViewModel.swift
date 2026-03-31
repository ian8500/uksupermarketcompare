import Foundation

final class AppCoordinatorViewModel: ObservableObject {
    @Published var path: [AppRoute] = []

    let store: ShoppingListStore
    private let dataProvider: SupermarketDataProviding
    private let basketService: BasketOptimising

    init(
        store: ShoppingListStore = ShoppingListStore(),
        dataProvider: SupermarketDataProviding = MockSupermarketDataService(),
        basketService: BasketOptimising? = nil
    ) {
        self.store = store
        self.dataProvider = dataProvider
        self.basketService = basketService ?? BasketOptimiserService(dataProvider: dataProvider)
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

    func openCreateList() {
        path.append(.createList)
    }

    func openSavedLists() {
        path.append(.savedLists)
    }

    func openSelection(for list: ShoppingList) {
        path.append(.supermarketSelection(list))
    }

    func openResults(_ result: BasketOptimisationResult) {
        path.append(.comparison(result))
    }

    func openSavedListDetail(_ list: ShoppingList) {
        path.append(.savedListDetail(list))
    }
}
