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
    case tomatoes
    case rice
    case yogurt
    case apples
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
        case .milk: return ["milk", "semi skimmed", "whole", "skimmed", "uht"]
        case .bread: return ["bread", "sliced", "wholemeal", "white", "seeded"]
        case .eggs: return ["eggs", "egg", "free range", "mixed weight"]
        case .butter: return ["butter", "spreadable", "salted", "unsalted"]
        case .pasta: return ["pasta", "spaghetti", "penne", "fusilli"]
        case .bakedBeans: return ["baked beans", "beans", "tinned beans"]
        case .bananas: return ["banana", "bananas", "fruit"]
        case .chickenBreast: return ["chicken breast", "chicken", "fillets", "fresh"]
        case .cereal: return ["cereal", "corn flakes", "wheat biscuits", "muesli", "granola"]
        case .cheese: return ["cheese", "cheddar", "mozzarella", "red leicester"]
        case .tomatoes: return ["tomato", "tomatoes", "salad"]
        case .rice: return ["rice", "basmati", "long grain"]
        case .yogurt: return ["yogurt", "yoghurt", "greek"]
        case .apples: return ["apple", "apples", "fruit"]
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

enum BasketComparisonMode: String, Codable, CaseIterable, Hashable {
    case cheapestPossible
    case cheapestSingleStoreOnly

    var title: String {
        switch self {
        case .cheapestPossible: return "Cheapest possible"
        case .cheapestSingleStoreOnly: return "Single-store only"
        }
    }
}

enum BrandPreference: String, Codable, CaseIterable, Hashable {
    case neutral
    case ownBrandPreferred
    case brandedPreferred
    case brandedOnly

    var title: String {
        switch self {
        case .neutral: return "No preference"
        case .ownBrandPreferred: return "Own-brand preferred"
        case .brandedPreferred: return "Branded preferred"
        case .brandedOnly: return "Branded only"
        }
    }
}

struct BasketUserPreferences: Codable, Hashable {
    var brandPreference: BrandPreference
    var avoidPremium: Bool
    var organicOnly: Bool

    static let `default` = BasketUserPreferences(brandPreference: .neutral, avoidPremium: false, organicOnly: false)
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
    let weightedUnitValue: Decimal
    let isValid: Bool
    let reasons: [String]
}

struct ItemSelectionResult: Identifiable, Codable, Hashable {
    let id: UUID
    let intent: GroceryIntent
    let supermarket: Supermarket
    let product: SupermarketProduct
    let quantity: Int
    let unitPrice: Decimal
    let unitPriceDescription: String
    let totalPrice: Decimal
    let matchQuality: MatchQuality
    let confidence: Decimal
    let reasons: [String]

    init(intent: GroceryIntent, supermarket: Supermarket, product: SupermarketProduct, matchQuality: MatchQuality, confidence: Decimal, reasons: [String]) {
        self.id = UUID()
        self.intent = intent
        self.supermarket = supermarket
        self.product = product
        self.quantity = intent.quantity
        self.unitPrice = product.price
        self.unitPriceDescription = "\(product.unitDescription) \(product.unitValue)"
        self.totalPrice = product.price * Decimal(intent.quantity)
        self.matchQuality = matchQuality
        self.confidence = confidence
        self.reasons = reasons
    }
}

struct SupermarketBasketTotal: Identifiable, Codable, Hashable {
    let id: UUID
    let supermarket: Supermarket
    let selections: [ItemSelectionResult]
    let unavailableItems: [GroceryIntent]
    let total: Decimal
    let missingItemsExplanation: String

    init(supermarket: Supermarket, selections: [ItemSelectionResult], unavailableItems: [GroceryIntent], missingItemsExplanation: String? = nil) {
        self.id = UUID()
        self.supermarket = supermarket
        self.selections = selections
        self.unavailableItems = unavailableItems
        self.total = selections.reduce(Decimal.zero) { $0 + $1.totalPrice }
        self.missingItemsExplanation = missingItemsExplanation ?? Self.defaultMissingItemsExplanation(for: unavailableItems)
    }

    static func defaultMissingItemsExplanation(for unavailableItems: [GroceryIntent]) -> String {
        guard !unavailableItems.isEmpty else { return "All requested items were matched." }
        let names = unavailableItems.map(\.userInput).joined(separator: ", ")
        return "Missing \(unavailableItems.count) item(s): \(names). Try broadening item names or adding more supermarkets."
    }
}

struct MixedBasketResult: Codable, Hashable {
    let selections: [ItemSelectionResult]
    let unavailableItems: [GroceryIntent]
    let total: Decimal
    let missingItemsExplanation: String

    init(selections: [ItemSelectionResult], unavailableItems: [GroceryIntent], missingItemsExplanation: String? = nil) {
        self.selections = selections
        self.unavailableItems = unavailableItems
        self.total = selections.reduce(Decimal.zero) { $0 + $1.totalPrice }
        self.missingItemsExplanation = missingItemsExplanation ?? SupermarketBasketTotal.defaultMissingItemsExplanation(for: unavailableItems)
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
    let selectedBasket: MixedBasketResult
    let comparisonMode: BasketComparisonMode
    let preferences: BasketUserPreferences
    let preferenceEffects: [String]?

    var mostExpensiveCompleteStoreTotal: Decimal? {
        let complete = supermarketTotals.filter { $0.unavailableItems.isEmpty }
        return complete.map(\.total).max()
    }

    var savingsVsMostExpensive: Decimal {
        guard let maxTotal = mostExpensiveCompleteStoreTotal else { return .zero }
        return maxTotal - selectedBasket.total
    }

    var savingsVsCheapestSingleStore: Decimal {
        guard let cheapestSingleStore else { return .zero }
        return cheapestSingleStore.total - selectedBasket.total
    }
}
