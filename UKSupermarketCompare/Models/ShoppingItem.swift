import Foundation

struct ShoppingItem: Identifiable, Codable, Hashable {
    let id: UUID
    var name: String
    var quantity: Int

    init(id: UUID = UUID(), name: String, quantity: Int) {
        self.id = id
        self.name = name
        self.quantity = quantity
    }
}
