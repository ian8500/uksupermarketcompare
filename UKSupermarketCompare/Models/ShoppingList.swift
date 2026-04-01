import Foundation

struct ShoppingList: Identifiable, Codable, Hashable {
    let id: UUID
    var title: String
    var createdAt: Date
    var lastComparedAt: Date?
    var items: [ShoppingItem]

    init(id: UUID = UUID(), title: String, createdAt: Date = Date(), lastComparedAt: Date? = nil, items: [ShoppingItem]) {
        self.id = id
        self.title = title
        self.createdAt = createdAt
        self.lastComparedAt = lastComparedAt
        self.items = items
    }
}
