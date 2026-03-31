import Foundation

protocol SupermarketDataProviding {
    func supermarkets() -> [Supermarket]
    func unitPrice(for itemName: String, at supermarket: Supermarket) -> Decimal
}

final class MockSupermarketDataService: SupermarketDataProviding {
    private let basePrices: [String: Decimal] = [
        "milk": 1.35,
        "bread": 1.10,
        "eggs": 2.25,
        "apples": 1.80,
        "bananas": 1.25,
        "rice": 2.50,
        "pasta": 1.15,
        "chicken": 4.95,
        "tomatoes": 1.65,
        "potatoes": 2.10
    ]

    private let adjustments: [String: Decimal] = [
        "Tesco": 1.00,
        "Sainsbury's": 1.04,
        "ASDA": 0.96,
        "Morrisons": 0.99,
        "Aldi": 0.91,
        "Lidl": 0.89
    ]

    func supermarkets() -> [Supermarket] {
        [
            Supermarket(name: "Tesco", description: "Strong own-brand range and wide UK coverage."),
            Supermarket(name: "Sainsbury's", description: "Quality-focused range with Nectar loyalty perks."),
            Supermarket(name: "ASDA", description: "Typically competitive prices on large baskets."),
            Supermarket(name: "Morrisons", description: "Balanced pricing and fresh produce options."),
            Supermarket(name: "Aldi", description: "Discount-first pricing, streamlined brand options."),
            Supermarket(name: "Lidl", description: "Low-cost staples and rotating weekly offers.")
        ]
    }

    func unitPrice(for itemName: String, at supermarket: Supermarket) -> Decimal {
        let key = itemName.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let base = basePrices[key] ?? 2.00
        let adjustment = adjustments[supermarket.name] ?? 1.00
        return base * adjustment
    }
}
