import Foundation

struct Supermarket: Identifiable, Codable, Hashable {
    let id: UUID
    var name: String
    var description: String

    init(id: UUID = UUID(), name: String, description: String) {
        self.id = id
        self.name = name
        self.description = description
    }
}


extension Decimal {
    func asGBP() -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "GBP"
        formatter.locale = Locale(identifier: "en_GB")
        return formatter.string(from: self as NSDecimalNumber) ?? "£0.00"
    }
}
