import Foundation

enum AppRoute: Hashable {
    case createList
    case supermarketSelection(ShoppingList)
    case comparison(BasketComparisonResult)
    case savedLists
    case savedListDetail(ShoppingList)
}
