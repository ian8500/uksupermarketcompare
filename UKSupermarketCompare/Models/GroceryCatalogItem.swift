import Foundation

struct GroceryCatalogItem: Identifiable, Codable, Hashable {
    let id: String
    let displayName: String
    let genericName: String
    let category: String
    let subcategory: String
    let commonSizes: [String]
    let commonUnits: [String]
    let keywords: [String]
    let defaultQuantityStep: Int
    let preferredMatchingTags: [String]

    var normalizedTokens: [String] {
        Set(([displayName, genericName] + keywords)
            .flatMap { $0.lowercased().split(whereSeparator: { !$0.isLetter && !$0.isNumber }) }
            .map(String.init))
        .sorted()
    }
}

struct GrocerySuggestion: Identifiable, Hashable {
    let id: String
    let item: GroceryCatalogItem
    let score: Int

    var hintText: String {
        let size = item.commonSizes.first ?? "Common pack"
        return "\(item.category.capitalized) • \(size)"
    }
}
