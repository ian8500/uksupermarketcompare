import Foundation

final class AppCoordinatorViewModel: ObservableObject {
    @Published var path: [AppRoute] = []

    let store: ShoppingListStore
    private let dataProvider: SupermarketDataProviding
    private let basketService: BasketComparing

    init(
        store: ShoppingListStore = ShoppingListStore(),
        dataProvider: SupermarketDataProviding = MockSupermarketDataService(),
        basketService: BasketComparing? = nil
    ) {
        self.store = store
        self.dataProvider = dataProvider
        self.basketService = basketService ?? BasketComparisonService(dataProvider: dataProvider)
    }

    func supermarkets() -> [Supermarket] {
        dataProvider.supermarkets()
    }

    func compare(list: ShoppingList, markets: [Supermarket]) -> BasketComparisonResult {
        basketService.compare(shoppingList: list, supermarkets: markets)
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

    func openResults(_ result: BasketComparisonResult) {
        path.append(.comparison(result))
    }

    func openSavedListDetail(_ list: ShoppingList) {
        path.append(.savedListDetail(list))
    }
}
