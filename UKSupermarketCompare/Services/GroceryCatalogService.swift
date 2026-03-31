import Foundation

protocol GroceryCatalogServing {
    var allItems: [GroceryCatalogItem] { get }
    func suggestions(for query: String, limit: Int) -> [GrocerySuggestion]
    func catalogItem(matching rawText: String) -> GroceryCatalogItem?
}

final class GroceryCatalogService: GroceryCatalogServing {
    let allItems: [GroceryCatalogItem]

    init(bundle: Bundle = .main, fileName: String = "GroceryCatalogSeed") {
        guard
            let url = bundle.url(forResource: fileName, withExtension: "json"),
            let data = try? Data(contentsOf: url),
            let decoded = try? JSONDecoder().decode([GroceryCatalogItem].self, from: data)
        else {
            self.allItems = []
            return
        }
        self.allItems = decoded
    }

    func suggestions(for query: String, limit: Int = 8) -> [GrocerySuggestion] {
        let normalized = normalize(query)
        guard !normalized.isEmpty else { return Array(allItems.prefix(limit)).map { GrocerySuggestion(id: $0.id, item: $0, score: 1) } }

        return allItems.compactMap { item in
            let score = score(item: item, query: normalized)
            guard score > 0 else { return nil }
            return GrocerySuggestion(id: item.id, item: item, score: score)
        }
        .sorted {
            if $0.score == $1.score {
                return $0.item.displayName < $1.item.displayName
            }
            return $0.score > $1.score
        }
        .prefix(limit)
        .map { $0 }
    }

    func catalogItem(matching rawText: String) -> GroceryCatalogItem? {
        let normalized = normalize(rawText)
        return suggestions(for: normalized, limit: 1).first?.item
    }

    private func score(item: GroceryCatalogItem, query: String) -> Int {
        let name = item.displayName.lowercased()
        let generic = item.genericName.lowercased()
        let keywords = item.keywords.map { $0.lowercased() }

        if name == query || generic == query { return 120 }

        var value = 0
        if name.hasPrefix(query) { value += 90 }
        if generic.hasPrefix(query) { value += 70 }
        if name.contains(query) { value += 55 }
        if generic.contains(query) { value += 45 }

        let keywordPrefixHits = keywords.filter { $0.hasPrefix(query) }.count
        let keywordContainsHits = keywords.filter { $0.contains(query) }.count
        value += keywordPrefixHits * 20
        value += keywordContainsHits * 8

        let queryTokens = Set(query.split(separator: " ").map(String.init))
        let tokenMatches = queryTokens.intersection(Set(item.normalizedTokens)).count
        value += tokenMatches * 18

        return value
    }

    private func normalize(_ value: String) -> String {
        value
            .lowercased()
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "  ", with: " ")
    }
}
