import Foundation

enum GroceryCategory: String, Codable, Hashable, CaseIterable {
    case milk
    case bread
    case eggs
    case butter
    case pasta
    case bakedBeans
    case bananas
    case chickenBreast
    case cereal
    case cheese
    case unknown

    var displayName: String {
        switch self {
        case .bakedBeans: return "Baked Beans"
        case .chickenBreast: return "Chicken Breast"
        default: return rawValue.capitalized
        }
    }

    var defaultKeywords: [String] {
        switch self {
        case .milk: return ["milk", "semi skimmed", "whole", "skimmed"]
        case .bread: return ["bread", "sliced", "wholemeal", "white"]
        case .eggs: return ["eggs", "egg", "free range"]
        case .butter: return ["butter", "spreadable"]
        case .pasta: return ["pasta", "spaghetti", "penne"]
        case .bakedBeans: return ["baked beans", "beans"]
        case .bananas: return ["banana", "bananas"]
        case .chickenBreast: return ["chicken breast", "chicken"]
        case .cereal: return ["cereal", "corn flakes", "wheat biscuits", "muesli"]
        case .cheese: return ["cheese", "cheddar"]
        case .unknown: return []
        }
    }
}

enum MatchQuality: Int, Codable, Hashable, Comparable {
    case exact = 3
    case acceptableEquivalent = 2
    case weakSubstitute = 1

    static func < (lhs: MatchQuality, rhs: MatchQuality) -> Bool {
        lhs.rawValue < rhs.rawValue
    }

    var label: String {
        switch self {
        case .exact: return "Exact"
        case .acceptableEquivalent: return "Equivalent"
        case .weakSubstitute: return "Substitute"
        }
    }
}

struct GroceryIntent: Identifiable, Codable, Hashable {
    let id: UUID
    let userInput: String
    let normalizedInput: String
    let category: GroceryCategory
    let quantity: Int
    let acceptedKeywords: [String]

    init(id: UUID = UUID(), userInput: String, category: GroceryCategory, quantity: Int) {
        let cleaned = userInput.trimmingCharacters(in: .whitespacesAndNewlines)
        self.id = id
        self.userInput = cleaned
        self.normalizedInput = cleaned.lowercased()
        self.category = category
        self.quantity = max(1, quantity)
        self.acceptedKeywords = category.defaultKeywords
    }
}

struct SupermarketProduct: Identifiable, Codable, Hashable {
    let id: UUID
    let supermarketName: String
    let name: String
    let category: GroceryCategory
    let subcategory: String
    let price: Decimal
    let size: String
    let brand: String
    let isOwnBrand: Bool
    let isPremium: Bool
    let isOrganic: Bool
    let unitDescription: String
    let unitValue: Decimal
    let tags: [String]

    init(
        id: UUID = UUID(),
        supermarketName: String,
        name: String,
        category: GroceryCategory,
        subcategory: String,
        price: Decimal,
        size: String,
        brand: String,
        isOwnBrand: Bool,
        isPremium: Bool,
        isOrganic: Bool,
        unitDescription: String,
        unitValue: Decimal,
        tags: [String]
    ) {
        self.id = id
        self.supermarketName = supermarketName
        self.name = name
        self.category = category
        self.subcategory = subcategory
        self.price = price
        self.size = size
        self.brand = brand
        self.isOwnBrand = isOwnBrand
        self.isPremium = isPremium
        self.isOrganic = isOrganic
        self.unitDescription = unitDescription
        self.unitValue = unitValue
        self.tags = tags.map { $0.lowercased() }
    }
}

struct ProductCandidate: Identifiable, Codable, Hashable {
    let id: UUID
    let intent: GroceryIntent
    let supermarket: Supermarket
    let product: SupermarketProduct
    let matchQuality: MatchQuality
    let confidence: Decimal
    let isValid: Bool
}

struct ItemSelectionResult: Identifiable, Codable, Hashable {
    let id: UUID
    let intent: GroceryIntent
    let supermarket: Supermarket
    let product: SupermarketProduct
    let quantity: Int
    let unitPrice: Decimal
    let totalPrice: Decimal
    let matchQuality: MatchQuality
    let confidence: Decimal

    init(intent: GroceryIntent, supermarket: Supermarket, product: SupermarketProduct, matchQuality: MatchQuality, confidence: Decimal) {
        self.id = UUID()
        self.intent = intent
        self.supermarket = supermarket
        self.product = product
        self.quantity = intent.quantity
        self.unitPrice = product.price
        self.totalPrice = product.price * Decimal(intent.quantity)
        self.matchQuality = matchQuality
        self.confidence = confidence
    }
}

struct SupermarketBasketTotal: Identifiable, Codable, Hashable {
    let id: UUID
    let supermarket: Supermarket
    let selections: [ItemSelectionResult]
    let unavailableItems: [GroceryIntent]
    let total: Decimal

    init(supermarket: Supermarket, selections: [ItemSelectionResult], unavailableItems: [GroceryIntent]) {
        self.id = UUID()
        self.supermarket = supermarket
        self.selections = selections
        self.unavailableItems = unavailableItems
        self.total = selections.reduce(Decimal.zero) { $0 + $1.totalPrice }
    }
}

struct MixedBasketResult: Codable, Hashable {
    let selections: [ItemSelectionResult]
    let unavailableItems: [GroceryIntent]
    let total: Decimal

    init(selections: [ItemSelectionResult], unavailableItems: [GroceryIntent]) {
        self.selections = selections
        self.unavailableItems = unavailableItems
        self.total = selections.reduce(Decimal.zero) { $0 + $1.totalPrice }
    }

    var supermarketsUsed: [String] {
        Array(Set(selections.map { $0.supermarket.name })).sorted()
    }
}

struct BasketOptimisationResult: Codable, Hashable {
    let shoppingList: ShoppingList
    let intents: [GroceryIntent]
    let supermarketTotals: [SupermarketBasketTotal]
    let cheapestSingleStore: SupermarketBasketTotal?
    let mixedBasket: MixedBasketResult

    var mostExpensiveCompleteStoreTotal: Decimal? {
        let complete = supermarketTotals.filter { $0.unavailableItems.isEmpty }
        return complete.map(\.total).max()
    }

    var savingsVsMostExpensive: Decimal {
        guard let maxTotal = mostExpensiveCompleteStoreTotal else { return .zero }
        return maxTotal - mixedBasket.total
    }

    var savingsVsCheapestSingleStore: Decimal {
        guard let cheapestSingleStore else { return .zero }
        return cheapestSingleStore.total - mixedBasket.total
    }
}
