import Foundation

protocol SupermarketDataProviding {
    func supermarkets() -> [Supermarket]
    func products(at supermarket: Supermarket) -> [SupermarketProduct]
}

final class MockSupermarketDataService: SupermarketDataProviding {
    private let markets: [Supermarket] = [
        Supermarket(name: "Tesco", description: "Strong own-brand range and wide UK coverage."),
        Supermarket(name: "Sainsbury's", description: "Quality-focused range with Nectar loyalty perks."),
        Supermarket(name: "ASDA", description: "Typically competitive prices on large baskets."),
        Supermarket(name: "Morrisons", description: "Balanced pricing and fresh produce options."),
        Supermarket(name: "Waitrose", description: "Premium-leaning range with quality fresh products.")
    ]

    private lazy var productsByStore: [String: [SupermarketProduct]] = buildProducts()

    func supermarkets() -> [Supermarket] {
        markets
    }

    func products(at supermarket: Supermarket) -> [SupermarketProduct] {
        productsByStore[supermarket.name, default: []]
    }

    private func buildProducts() -> [String: [SupermarketProduct]] {
        [
            "Tesco": commonRange(
                store: "Tesco",
                ownBrand: "Tesco",
                budgetFactor: 1.0,
                hasMorePremium: true
            ),
            "Sainsbury's": commonRange(
                store: "Sainsbury's",
                ownBrand: "Sainsbury's",
                budgetFactor: 1.05,
                hasMorePremium: false
            ),
            "ASDA": commonRange(
                store: "ASDA",
                ownBrand: "ASDA",
                budgetFactor: 0.93,
                hasMorePremium: false
            ),
            "Morrisons": commonRange(
                store: "Morrisons",
                ownBrand: "Morrisons",
                budgetFactor: 1.0,
                hasMorePremium: false
            ),
            "Waitrose": commonRange(
                store: "Waitrose",
                ownBrand: "Essential Waitrose",
                budgetFactor: 1.16,
                hasMorePremium: true
            )
        ]
    }

    private func commonRange(store: String, ownBrand: String, budgetFactor: Double, hasMorePremium: Bool) -> [SupermarketProduct] {
        let premiumMultiplier: Double = hasMorePremium ? 1.0 : 0.96
        return [
            p("\(ownBrand) Semi Skimmed Milk 2L", .milk, "semi-skimmed", adjusted(1.55, budgetFactor), "2L", ownBrand, true, false, false, "per litre", adjusted(0.775, budgetFactor), ["milk", "semi skimmed"]),
            p("Cravendale Fresh Milk 2L", .milk, "semi-skimmed", adjusted(2.10, premiumMultiplier * budgetFactor), "2L", "Cravendale", false, false, false, "per litre", adjusted(1.05, premiumMultiplier * budgetFactor), ["milk", "branded"]),
            p("\(store) Organic Whole Milk 2L", .milk, "whole", adjusted(2.40, premiumMultiplier * budgetFactor), "2L", ownBrand, true, true, true, "per litre", adjusted(1.20, premiumMultiplier * budgetFactor), ["milk", "organic", "premium"]),

            p("\(ownBrand) White Bread 800g", .bread, "white sliced", adjusted(0.85, budgetFactor), "800g", ownBrand, true, false, false, "per kg", adjusted(1.0625, budgetFactor), ["bread", "white", "sliced"]),
            p("Warburtons Toastie 800g", .bread, "white sliced", adjusted(1.45, budgetFactor), "800g", "Warburtons", false, false, false, "per kg", adjusted(1.8125, budgetFactor), ["bread", "branded"]),
            p("\(store) Organic Seeded Loaf 700g", .bread, "seeded", adjusted(2.05, premiumMultiplier * budgetFactor), "700g", ownBrand, true, true, true, "per kg", adjusted(2.9285, premiumMultiplier * budgetFactor), ["bread", "organic", "seeded"]),

            p("\(ownBrand) Eggs 12", .eggs, "free range", adjusted(2.05, budgetFactor), "12 pack", ownBrand, true, false, false, "per egg", adjusted(0.171, budgetFactor), ["eggs", "free range"]),
            p("Happy Egg Co Large Eggs 10", .eggs, "free range", adjusted(2.55, budgetFactor), "10 pack", "Happy Egg Co", false, false, false, "per egg", adjusted(0.255, budgetFactor), ["eggs", "branded"]),

            p("\(ownBrand) Salted Butter 250g", .butter, "salted", adjusted(1.95, budgetFactor), "250g", ownBrand, true, false, false, "per kg", adjusted(7.8, budgetFactor), ["butter", "salted"]),
            p("Lurpak Slightly Salted 400g", .butter, "spreadable", adjusted(3.65, budgetFactor), "400g", "Lurpak", false, false, false, "per kg", adjusted(9.125, budgetFactor), ["butter", "spreadable", "branded"]),

            p("\(ownBrand) Penne Pasta 500g", .pasta, "penne", adjusted(0.86, budgetFactor), "500g", ownBrand, true, false, false, "per kg", adjusted(1.72, budgetFactor), ["pasta", "penne"]),
            p("Barilla Spaghetti No.5 500g", .pasta, "spaghetti", adjusted(1.60, budgetFactor), "500g", "Barilla", false, false, false, "per kg", adjusted(3.2, budgetFactor), ["pasta", "spaghetti", "branded"]),

            p("\(ownBrand) Baked Beans 4x420g", .bakedBeans, "tinned", adjusted(2.15, budgetFactor), "4 pack", ownBrand, true, false, false, "per can", adjusted(0.5375, budgetFactor), ["baked beans", "beans"]),
            p("Heinz Baked Beans 4x415g", .bakedBeans, "tinned", adjusted(3.25, budgetFactor), "4 pack", "Heinz", false, false, false, "per can", adjusted(0.8125, budgetFactor), ["baked beans", "branded"]),

            p("\(ownBrand) Bananas", .bananas, "produce", adjusted(1.05, budgetFactor), "5 pack", ownBrand, true, false, false, "per item", adjusted(0.21, budgetFactor), ["banana", "fruit"]),
            p("\(store) Organic Bananas", .bananas, "produce", adjusted(1.35, premiumMultiplier * budgetFactor), "5 pack", ownBrand, true, true, true, "per item", adjusted(0.27, premiumMultiplier * budgetFactor), ["banana", "organic"]),

            p("\(ownBrand) Chicken Breast Fillets 550g", .chickenBreast, "fresh", adjusted(4.35, budgetFactor), "550g", ownBrand, true, false, false, "per kg", adjusted(7.91, budgetFactor), ["chicken breast", "fillets"]),
            p("RSPCA Organic Chicken Breast 500g", .chickenBreast, "fresh", adjusted(6.85, premiumMultiplier * budgetFactor), "500g", "RSPCA Assured", false, true, true, "per kg", adjusted(13.7, premiumMultiplier * budgetFactor), ["chicken breast", "organic", "premium"]),

            p("\(ownBrand) Corn Flakes 500g", .cereal, "corn flakes", adjusted(1.25, budgetFactor), "500g", ownBrand, true, false, false, "per kg", adjusted(2.5, budgetFactor), ["cereal", "corn flakes"]),
            p("Kellogg's Corn Flakes 450g", .cereal, "corn flakes", adjusted(2.30, budgetFactor), "450g", "Kellogg's", false, false, false, "per kg", adjusted(5.11, budgetFactor), ["cereal", "branded"]),

            p("\(ownBrand) Mature Cheddar 400g", .cheese, "cheddar", adjusted(2.85, budgetFactor), "400g", ownBrand, true, false, false, "per kg", adjusted(7.125, budgetFactor), ["cheese", "cheddar"]),
            p("Cathedral City Mature Cheddar 350g", .cheese, "cheddar", adjusted(4.25, budgetFactor), "350g", "Cathedral City", false, false, false, "per kg", adjusted(12.14, budgetFactor), ["cheese", "branded"]),

            p("\(ownBrand) Salad Tomatoes 6 Pack", .tomatoes, "produce", adjusted(1.10, budgetFactor), "6 pack", ownBrand, true, false, false, "per item", adjusted(0.183, budgetFactor), ["tomatoes", "salad"]),
            p("\(ownBrand) Basmati Rice 1kg", .rice, "dry", adjusted(1.95, budgetFactor), "1kg", ownBrand, true, false, false, "per kg", adjusted(1.95, budgetFactor), ["rice", "basmati"]),
            p("\(ownBrand) Greek Style Yogurt 500g", .yogurt, "dairy", adjusted(1.35, budgetFactor), "500g", ownBrand, true, false, false, "per kg", adjusted(2.7, budgetFactor), ["yogurt", "greek"]),
            p("\(ownBrand) Gala Apples 6 Pack", .apples, "produce", adjusted(1.45, budgetFactor), "6 pack", ownBrand, true, false, false, "per item", adjusted(0.241, budgetFactor), ["apple", "fruit"])
        ]
    }

    private func adjusted(_ value: Double, _ factor: Double) -> Decimal {
        Decimal((value * factor * 1000).rounded() / 1000)
    }

    private func p(
        _ name: String,
        _ category: GroceryCategory,
        _ subcategory: String,
        _ price: Decimal,
        _ size: String,
        _ brand: String,
        _ own: Bool,
        _ premium: Bool,
        _ organic: Bool,
        _ unitDescription: String,
        _ unitValue: Decimal,
        _ tags: [String]
    ) -> SupermarketProduct {
        let market = markets.first {
            name.contains($0.name) || brand.contains($0.name) || ($0.name == "Waitrose" && name.contains("Essential Waitrose"))
        }?.name ?? "Tesco"

        return SupermarketProduct(
            supermarketName: market,
            name: name,
            category: category,
            subcategory: subcategory,
            price: price,
            size: size,
            brand: brand,
            isOwnBrand: own,
            isPremium: premium,
            isOrganic: organic,
            unitDescription: unitDescription,
            unitValue: unitValue,
            tags: tags
        )
    }
}
