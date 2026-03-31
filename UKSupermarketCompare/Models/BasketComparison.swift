import Foundation

struct BasketPriceLine: Identifiable, Codable, Hashable {
    let id: UUID
    let supermarketName: String
    let subtotal: Decimal

    init(id: UUID = UUID(), supermarketName: String, subtotal: Decimal) {
        self.id = id
        self.supermarketName = supermarketName
        self.subtotal = subtotal
    }
}

struct BasketComparisonResult: Codable, Hashable {
    let shoppingList: ShoppingList
    let prices: [BasketPriceLine]

    var bestOption: BasketPriceLine? {
        prices.min { $0.subtotal < $1.subtotal }
    }
}
