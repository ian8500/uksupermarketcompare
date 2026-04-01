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

enum SuggestionOrigin: String {
    case backend
    case fallback
}

struct GrocerySuggestion: Identifiable, Hashable {
    let id: String
    let item: GroceryCatalogItem
    let score: Int
    let origin: SuggestionOrigin

    init(id: String, item: GroceryCatalogItem, score: Int, origin: SuggestionOrigin = .fallback) {
        self.id = id
        self.item = item
        self.score = score
        self.origin = origin
    }

    var primaryText: String {
        item.displayName
    }

    var hintText: String {
        let size = item.commonSizes.first ?? "Common pack"
        let brand = item.preferredMatchingTags.first(where: { !$0.isEmpty })

        if let brand {
            return "\(item.category.capitalized) • \(brand.capitalized) • \(size)"
        }

        return "\(item.category.capitalized) • \(size)"
    }
}
