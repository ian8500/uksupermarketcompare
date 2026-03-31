import SwiftUI

@main
struct UKSupermarketCompareApp: App {
    @StateObject private var coordinator = AppCoordinatorViewModel()

    var body: some Scene {
        WindowGroup {
            NavigationStack(path: $coordinator.path) {
                HomeView(viewModel: HomeViewModel())
                    .navigationDestination(for: AppRoute.self) { route in
                        switch route {
                        case .createList:
                            CreateShoppingListView(viewModel: CreateShoppingListViewModel(coordinator: coordinator))
                        case .supermarketSelection(let shoppingList):
                            SupermarketSelectionView(viewModel: SupermarketSelectionViewModel(shoppingList: shoppingList, coordinator: coordinator))
                        case .comparison(let result):
                            BasketComparisonResultsView(viewModel: BasketComparisonResultsViewModel(result: result, store: coordinator.store))
                        case .savedLists:
                            SavedListsView(viewModel: SavedListsViewModel(store: coordinator.store))
                        case .savedListDetail(let list):
                            SavedListDetailView(shoppingList: list)
                        }
                    }
            }
            .environmentObject(coordinator)
        }
    }
}
