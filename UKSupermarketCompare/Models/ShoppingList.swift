import Foundation

struct ShoppingList: Identifiable, Codable, Hashable {
    let id: UUID
    var title: String
    var createdAt: Date
    var items: [ShoppingItem]

    init(id: UUID = UUID(), title: String, createdAt: Date = Date(), items: [ShoppingItem]) {
        self.id = id
        self.title = title
        self.createdAt = createdAt
        self.items = items
    }
}
