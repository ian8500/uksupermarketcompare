import Foundation

enum AppRoute: Hashable {
    case createList
    case supermarketSelection(ShoppingList)
    case comparison(BasketOptimisationResult)
    case savedLists
    case savedListDetail(ShoppingList)
}
