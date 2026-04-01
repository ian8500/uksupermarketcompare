import Foundation

@MainActor
final class CreateShoppingListViewModel: ObservableObject {
    @Published var listTitle = "Weekly Shop"
    @Published var itemName = "" {
        didSet { scheduleSuggestionRefresh() }
    }
    @Published var quantity = 1
    @Published private(set) var items: [ShoppingItem] = []
    @Published private(set) var suggestions: [GrocerySuggestion] = []
    @Published private(set) var suggestionSource: SuggestionOrigin = .fallback

    let weeklyEssentials = ["Milk", "Bread", "Eggs", "Bananas", "Butter", "Pasta"]
    private let popularItems = ["milk", "bread", "eggs", "bananas", "butter", "pasta", "cheese", "chicken", "rice", "tomatoes"]

    private let coordinator: AppCoordinatorViewModel
    private let catalogService: GroceryCatalogServing
    private let backendAutocompleteService: BackendAutocompleteServing?
    private var suggestionTask: Task<Void, Never>?

    init(
        coordinator: AppCoordinatorViewModel,
        catalogService: GroceryCatalogServing,
        backendAutocompleteService: BackendAutocompleteServing? = nil
    ) {
        self.coordinator = coordinator
        self.catalogService = catalogService
        self.backendAutocompleteService = backendAutocompleteService
        self.suggestions = catalogService.suggestions(for: "", limit: 6)
    }

    deinit {
        suggestionTask?.cancel()
    }

    var canAddItem: Bool {
        !itemName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var canContinue: Bool {
        !items.isEmpty && !listTitle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var recentItems: [String] {
        coordinator.store.recentItems
    }

    func applySuggestion(_ suggestion: GrocerySuggestion) {
        itemName = suggestion.item.displayName
        quantity = max(1, suggestion.item.defaultQuantityStep)
    }

    func addSuggestion(_ suggestion: GrocerySuggestion) {
        applySuggestion(suggestion)
        addItem()
    }

    func addItem() {
        guard canAddItem else { return }
        let parsed = parseQuantityPrefix(from: itemName)
        let cleanedName = parsed.name
        let resolvedName = catalogService.catalogItem(matching: cleanedName)?.displayName ?? cleanedName.capitalized
        let resolvedQuantity = parsed.quantity ?? quantity
        items.append(ShoppingItem(name: resolvedName, quantity: max(resolvedQuantity, 1)))
        itemName = ""
        quantity = 1
        refreshFallbackSuggestions(for: "")
        print("[Analytics] item_added name=\(resolvedName) qty=\(resolvedQuantity)")
    }

    func addRecentItem(_ name: String) {
        itemName = name
        quantity = 1
        addItem()
    }

    func quickAddEssential(_ name: String) {
        itemName = name
        quantity = 1
        addItem()
    }

    func updateQuantity(for itemID: UUID, delta: Int) {
        guard let index = items.firstIndex(where: { $0.id == itemID }) else { return }
        items[index].quantity = max(1, items[index].quantity + delta)
    }

    func setQuantity(for itemID: UUID, to quantity: Int) {
        guard let index = items.firstIndex(where: { $0.id == itemID }) else { return }
        items[index].quantity = min(99, max(1, quantity))
    }

    func deleteItem(at offsets: IndexSet) {
        items.remove(atOffsets: offsets)
    }

    func continueToSupermarketSelection() {
        guard canContinue else { return }
        let list = ShoppingList(title: listTitle.trimmingCharacters(in: .whitespacesAndNewlines), items: items)
        coordinator.store.rememberItems(from: items)
        coordinator.openSelection(for: list)
        print("[Analytics] basket_started items=\(items.count)")
    }

    private func scheduleSuggestionRefresh() {
        suggestionTask?.cancel()
        let parsed = parseQuantityPrefix(from: itemName)
        refreshFallbackSuggestions(for: parsed.name)

        let query = parsed.name
        guard !query.isEmpty else { return }

        suggestionTask = Task { [weak self] in
            do {
                try await Task.sleep(nanoseconds: 200_000_000)
                guard !Task.isCancelled else { return }
                await self?.loadBackendSuggestions(for: query)
            } catch {
                // Cancellation only.
            }
        }
    }

    private func loadBackendSuggestions(for query: String) async {
        guard let backendAutocompleteService else { return }

        do {
            let remote = try await backendAutocompleteService.autocomplete(query: query, limit: 8)
            guard !Task.isCancelled else { return }
            if !remote.isEmpty {
                suggestions = rankSuggestions(remote, query: query).prefix(8).map { $0 }
                suggestionSource = .backend
                print("[Suggestions][source] backend query=\(query) count=\(suggestions.count)")
                return
            }
            suggestionSource = .fallback
            print("[Suggestions][source] fallback query=\(query) reason=empty_backend")
        } catch {
            suggestionSource = .fallback
            print("[Suggestions][backend][error] query=\(query) message=\(error.localizedDescription)")
        }
    }

    private func refreshFallbackSuggestions(for query: String) {
        let base = catalogService.suggestions(for: query, limit: 40)
        suggestions = rankSuggestions(base, query: query).prefix(8).map { $0 }
        suggestionSource = .fallback
        print("[Suggestions][source] fallback query=\(query) count=\(suggestions.count)")
    }

    private func parseQuantityPrefix(from raw: String) -> (name: String, quantity: Int?) {
        let cleaned = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        let tokens = cleaned.split(separator: " ", omittingEmptySubsequences: true)
        guard let first = tokens.first, let parsedQty = Int(first), parsedQty > 0 else {
            return (cleaned, nil)
        }

        let remainder = tokens.dropFirst().joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
        guard !remainder.isEmpty else { return (cleaned, nil) }
        return (remainder, min(parsedQty, 99))
    }

    private func rankSuggestions(_ candidates: [GrocerySuggestion], query: String) -> [GrocerySuggestion] {
        let normalizedQuery = normalize(query)
        let queryTokens = normalizedQuery.split(separator: " ").map(String.init)

        return candidates
            .map { suggestion in
                let itemName = normalize(suggestion.item.displayName)
                let groceryIntentBoost = suggestion.item.category.lowercased().contains("grocery") ? 60 : 0
                let recentBoost = recentItems.firstIndex(where: { normalize($0) == itemName }).map { max(8, 70 - ($0 * 7)) } ?? 0
                let popularityBoost = popularItems.contains(where: { itemName.contains($0) }) ? 32 : 0
                let exactBoost = itemName == normalizedQuery ? 260 : 0
                let brandBoost = {
                    let brand = suggestion.item.preferredMatchingTags.joined(separator: " ").lowercased()
                    guard !brand.isEmpty, !normalizedQuery.isEmpty else { return 0 }
                    return brand.contains(normalizedQuery) ? 30 : 0
                }()

                let fuzzyBoost: Int = {
                    guard !normalizedQuery.isEmpty else { return 0 }
                    if itemName.contains(normalizedQuery) { return 30 }
                    let distances = itemName.split(separator: " ").map(String.init).map { levenshteinDistance($0, normalizedQuery) }
                    if distances.contains(where: { $0 <= 1 && normalizedQuery.count > 3 }) { return 24 }
                    return 0
                }()

                let partialTokenBoost = queryTokens.reduce(into: 0) { total, token in
                    if itemName.hasPrefix(token) { total += 40 }
                    else if itemName.contains(token) { total += 16 }
                }

                let adjustedScore = suggestion.score + groceryIntentBoost + recentBoost + popularityBoost + exactBoost + fuzzyBoost + partialTokenBoost + brandBoost
                return GrocerySuggestion(id: suggestion.id, item: suggestion.item, score: adjustedScore, origin: suggestion.origin)
            }
            .sorted {
                if $0.score == $1.score {
                    return $0.item.displayName < $1.item.displayName
                }
                return $0.score > $1.score
            }
    }

    private func normalize(_ value: String) -> String {
        value.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
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
                current.append(min(previous[j + 1] + 1, current[j] + 1, previous[j] + substitutionCost))
            }
            previous = current
        }
        return previous[b.count]
    }
}
