import Foundation

protocol GroceryCatalogServing {
    var allItems: [GroceryCatalogItem] { get }
    func suggestions(for query: String, limit: Int) -> [GrocerySuggestion]
    func catalogItem(matching rawText: String) -> GroceryCatalogItem?
}

protocol BackendAutocompleteServing {
    func autocomplete(query: String, limit: Int) async throws -> [GrocerySuggestion]
}

final class BackendAutocompleteService: BackendAutocompleteServing {
    private let session: URLSession
    private let autocompleteURL: URL

    init?(session: URLSession = .shared) {
        let environment = ProcessInfo.processInfo.environment

        if let searchURL = environment["LIVE_SUPERMARKET_SEARCH_URL"], let parsed = URL(string: searchURL) {
            self.autocompleteURL = parsed
        } else if
            let catalogURLRaw = environment["LIVE_SUPERMARKET_DATA_URL"],
            let catalogURL = URL(string: catalogURLRaw)
        {
            self.autocompleteURL = catalogURL.deletingLastPathComponent().appendingPathComponent("autocomplete")
        } else {
            return nil
        }

        self.session = session
    }

    func autocomplete(query: String, limit: Int) async throws -> [GrocerySuggestion] {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return [] }

        var components = URLComponents(url: autocompleteURL, resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "q", value: query),
            URLQueryItem(name: "limit", value: String(limit))
        ]

        guard let url = components?.url else {
            throw URLError(.badURL)
        }

        var request = URLRequest(url: url)
        request.timeoutInterval = 2.0
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, (200..<300).contains(httpResponse.statusCode) else {
            throw URLError(.badServerResponse)
        }

        let payload = try JSONDecoder().decode(AutocompleteResponse.self, from: data)
        return payload.suggestions.map { $0.asSuggestion }
    }
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
        guard !normalized.isEmpty else {
            return Array(allItems.prefix(limit)).map { GrocerySuggestion(id: $0.id, item: $0, score: 1) }
        }

        let queryTokens = tokens(from: normalized)

        return allItems.compactMap { item in
            let score = score(item: item, query: normalized, queryTokens: queryTokens)
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

    private func score(item: GroceryCatalogItem, query: String, queryTokens: [String]) -> Int {
        let name = normalize(item.displayName)
        let generic = normalize(item.genericName)
        let keywords = item.keywords.map(normalize)
        let itemTokens = item.normalizedTokens

        if name == query || generic == query || keywords.contains(query) { return 220 }

        var value = 0

        if name.hasPrefix(query) { value += 140 }
        if generic.hasPrefix(query) { value += 120 }
        if keywords.contains(where: { $0.hasPrefix(query) }) { value += 90 }

        if name.contains(query) { value += 85 }
        if generic.contains(query) { value += 72 }
        value += keywords.filter { $0.contains(query) }.count * 22

        let tokenSet = Set(queryTokens)
        let directTokenHits = tokenSet.intersection(Set(itemTokens)).count
        value += directTokenHits * 32

        let prefixTokenHits = queryTokens.filter { queryToken in
            itemTokens.contains(where: { $0.hasPrefix(queryToken) })
        }.count
        value += prefixTokenHits * 20

        let closeTokenHits = queryTokens.filter { queryToken in
            itemTokens.contains(where: { levenshteinDistance($0, queryToken) == 1 && min($0.count, queryToken.count) > 3 })
        }.count
        value += closeTokenHits * 10

        if queryTokens.count > 1 && queryTokens.allSatisfy({ token in name.contains(token) || generic.contains(token) }) {
            value += 36
        }

        return value
    }

    private func normalize(_ value: String) -> String {
        value
            .lowercased()
            .folding(options: .diacriticInsensitive, locale: .current)
            .replacingOccurrences(of: "[^a-z0-9 ]", with: " ", options: .regularExpression)
            .replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func tokens(from value: String) -> [String] {
        normalize(value).split(separator: " ").map(String.init)
    }

    private func levenshteinDistance(_ lhs: String, _ rhs: String) -> Int {
        if lhs == rhs { return 0 }
        if lhs.isEmpty { return rhs.count }
        if rhs.isEmpty { return lhs.count }

        let a = Array(lhs)
        let b = Array(rhs)
        var previous = Array(0...b.count)

        for (i, charA) in a.enumerated() {
            var current = [i + 1]
            for (j, charB) in b.enumerated() {
                let substitutionCost = charA == charB ? 0 : 1
                let next = min(
                    previous[j + 1] + 1,
                    current[j] + 1,
                    previous[j] + substitutionCost
                )
                current.append(next)
            }
            previous = current
        }
        return previous[b.count]
    }
}

private struct AutocompleteResponse: Decodable {
    let suggestions: [BackendAutocompleteSuggestion]
}

private struct BackendAutocompleteSuggestion: Decodable {
    let suggestion: String
    let displayName: String
    let brand: String
    let size: String
    let category: String
    let score: Double

    var asSuggestion: GrocerySuggestion {
        let cleanedBrand = brand.trimmingCharacters(in: .whitespacesAndNewlines)
        let tags = cleanedBrand.isEmpty ? [] : [cleanedBrand]
        let item = GroceryCatalogItem(
            id: suggestion,
            displayName: displayName,
            genericName: displayName,
            category: category,
            subcategory: category,
            commonSizes: size.isEmpty ? [] : [size],
            commonUnits: [],
            keywords: [displayName],
            defaultQuantityStep: 1,
            preferredMatchingTags: tags
        )

        return GrocerySuggestion(
            id: suggestion,
            item: item,
            score: Int(score * 1_000),
            origin: .backend
        )
    }
}
