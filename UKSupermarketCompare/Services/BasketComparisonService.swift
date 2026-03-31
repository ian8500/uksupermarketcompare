import Foundation

protocol BasketComparing {
    func compare(shoppingList: ShoppingList, supermarkets: [Supermarket]) -> BasketComparisonResult
}

final class BasketComparisonService: BasketComparing {
    private let dataProvider: SupermarketDataProviding

    init(dataProvider: SupermarketDataProviding) {
        self.dataProvider = dataProvider
    }

    func compare(shoppingList: ShoppingList, supermarkets: [Supermarket]) -> BasketComparisonResult {
        let lines = supermarkets.map { market in
            let total = shoppingList.items.reduce(Decimal.zero) { partial, item in
                let unitPrice = dataProvider.unitPrice(for: item.name, at: market)
                let qty = Decimal(item.quantity)
                return partial + (unitPrice * qty)
            }
            return BasketPriceLine(supermarketName: market.name, subtotal: total)
        }
        return BasketComparisonResult(shoppingList: shoppingList, prices: lines.sorted { $0.subtotal < $1.subtotal })
    }
}
