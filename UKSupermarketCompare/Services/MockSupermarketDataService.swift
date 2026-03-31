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
            "Tesco": [
                p("Tesco Semi Skimmed Milk 2L", .milk, "semi-skimmed", 1.55, "2L", "Tesco", true, false, false, "per litre", 0.775, ["milk", "semi skimmed", "fresh"]),
                p("Tesco Whole Milk 2L", .milk, "whole", 1.60, "2L", "Tesco", true, false, false, "per litre", 0.80, ["milk", "whole"]),
                p("Tesco Finest Organic Milk 2L", .milk, "whole", 2.35, "2L", "Tesco Finest", true, true, true, "per litre", 1.175, ["milk", "organic", "premium"]),
                p("Tesco Medium Sliced White Bread 800g", .bread, "white sliced", 0.85, "800g", "Tesco", true, false, false, "per 100g", 0.10625, ["bread", "white", "sliced"]),
                p("Warburtons Wholemeal Medium 800g", .bread, "wholemeal sliced", 1.45, "800g", "Warburtons", false, false, false, "per 100g", 0.18125, ["bread", "wholemeal"]),
                p("Tesco British Eggs Mixed Weight 12", .eggs, "mixed weight", 2.10, "12 pack", "Tesco", true, false, false, "per egg", 0.175, ["eggs", "mixed"]),
                p("Tesco Salted Butter 250g", .butter, "salted", 1.99, "250g", "Tesco", true, false, false, "per 100g", 0.796, ["butter", "salted"]),
                p("Tesco Spreadable Blend 500g", .butter, "spreadable blend", 2.39, "500g", "Tesco", true, false, false, "per 100g", 0.478, ["spreadable", "butter", "blend"]),
                p("Tesco Penne Pasta 500g", .pasta, "penne", 0.89, "500g", "Tesco", true, false, false, "per 100g", 0.178, ["pasta", "penne"]),
                p("Heinz Baked Beans 4x415g", .bakedBeans, "tinned", 3.20, "4 pack", "Heinz", false, false, false, "per can", 0.80, ["baked beans", "beans"]),
                p("Tesco Baked Beans 4x420g", .bakedBeans, "tinned", 2.10, "4 pack", "Tesco", true, false, false, "per can", 0.525, ["baked beans", "beans"]),
                p("Tesco Fairtrade Bananas", .bananas, "produce", 1.05, "5 pack", "Tesco", true, false, false, "per banana", 0.21, ["banana", "fruit"]),
                p("Tesco British Chicken Breast Fillets", .chickenBreast, "fresh", 4.35, "550g", "Tesco", true, false, false, "per 100g", 0.79, ["chicken breast", "fillets"]),
                p("Tesco Corn Flakes 500g", .cereal, "corn flakes", 1.25, "500g", "Tesco", true, false, false, "per 100g", 0.25, ["cereal", "corn flakes"]),
                p("Tesco Mature Cheddar 400g", .cheese, "cheddar", 2.85, "400g", "Tesco", true, false, false, "per 100g", 0.7125, ["cheese", "cheddar"]),
                p("Tesco Finest Vintage Cheddar 300g", .cheese, "cheddar", 3.95, "300g", "Tesco Finest", true, true, false, "per 100g", 1.316, ["cheese", "cheddar", "premium"])
            ],
            "Sainsbury's": [
                p("Sainsbury's Semi Skimmed Milk 2L", .milk, "semi-skimmed", 1.62, "2L", "Sainsbury's", true, false, false, "per litre", 0.81, ["milk", "semi skimmed"]),
                p("Sainsbury's Whole Milk 2L", .milk, "whole", 1.66, "2L", "Sainsbury's", true, false, false, "per litre", 0.83, ["milk", "whole"]),
                p("Sainsbury's Soft White Bread 800g", .bread, "white sliced", 0.89, "800g", "Sainsbury's", true, false, false, "per 100g", 0.111, ["bread", "white"]),
                p("Sainsbury's Wholemeal Bread 800g", .bread, "wholemeal sliced", 0.95, "800g", "Sainsbury's", true, false, false, "per 100g", 0.119, ["bread", "wholemeal"]),
                p("Sainsbury's Eggs Mixed Weight 12", .eggs, "mixed weight", 2.08, "12 pack", "Sainsbury's", true, false, false, "per egg", 0.173, ["eggs", "mixed"]),
                p("Sainsbury's Salted Butter 250g", .butter, "salted", 2.05, "250g", "Sainsbury's", true, false, false, "per 100g", 0.82, ["butter"]),
                p("Sainsbury's Lighter Spread 500g", .butter, "spreadable blend", 1.95, "500g", "Sainsbury's", true, false, false, "per 100g", 0.39, ["spreadable", "blend"]),
                p("Sainsbury's Fusilli Pasta 500g", .pasta, "fusilli", 0.92, "500g", "Sainsbury's", true, false, false, "per 100g", 0.184, ["pasta", "fusilli"]),
                p("Sainsbury's Baked Beans 4x420g", .bakedBeans, "tinned", 2.25, "4 pack", "Sainsbury's", true, false, false, "per can", 0.5625, ["beans", "baked beans"]),
                p("Sainsbury's Bananas", .bananas, "produce", 1.10, "5 pack", "Sainsbury's", true, false, false, "per banana", 0.22, ["banana"]),
                p("Sainsbury's Chicken Breast Fillets", .chickenBreast, "fresh", 4.55, "550g", "Sainsbury's", true, false, false, "per 100g", 0.827, ["chicken breast"]),
                p("Sainsbury's Wheat Biscuits 24", .cereal, "wheat biscuits", 1.39, "24 pack", "Sainsbury's", true, false, false, "per biscuit", 0.058, ["cereal", "wheat biscuits"]),
                p("Sainsbury's Mature Cheddar 400g", .cheese, "cheddar", 2.95, "400g", "Sainsbury's", true, false, false, "per 100g", 0.7375, ["cheddar", "cheese"])
            ],
            "ASDA": [
                p("ASDA Semi Skimmed Milk 2L", .milk, "semi-skimmed", 1.49, "2L", "ASDA", true, false, false, "per litre", 0.745, ["milk"]),
                p("ASDA Whole Milk 2L", .milk, "whole", 1.52, "2L", "ASDA", true, false, false, "per litre", 0.76, ["milk"]),
                p("ASDA White Bread 800g", .bread, "white sliced", 0.75, "800g", "ASDA", true, false, false, "per 100g", 0.094, ["bread", "white"]),
                p("ASDA Wholemeal Bread 800g", .bread, "wholemeal sliced", 0.79, "800g", "ASDA", true, false, false, "per 100g", 0.099, ["bread", "wholemeal"]),
                p("ASDA Mixed Weight Eggs 12", .eggs, "mixed weight", 1.99, "12 pack", "ASDA", true, false, false, "per egg", 0.166, ["eggs"]),
                p("ASDA Salted Butter 250g", .butter, "salted", 1.89, "250g", "ASDA", true, false, false, "per 100g", 0.756, ["butter"]),
                p("ASDA Spreadable 500g", .butter, "spreadable blend", 1.75, "500g", "ASDA", true, false, false, "per 100g", 0.35, ["spreadable", "blend"]),
                p("ASDA Penne Pasta 500g", .pasta, "penne", 0.74, "500g", "ASDA", true, false, false, "per 100g", 0.148, ["pasta"]),
                p("ASDA Baked Beans 4x420g", .bakedBeans, "tinned", 1.85, "4 pack", "ASDA", true, false, false, "per can", 0.462, ["beans", "baked beans"]),
                p("ASDA Bananas", .bananas, "produce", 0.98, "5 pack", "ASDA", true, false, false, "per banana", 0.196, ["banana"]),
                p("ASDA Chicken Breast Fillets", .chickenBreast, "fresh", 4.10, "550g", "ASDA", true, false, false, "per 100g", 0.745, ["chicken breast"]),
                p("ASDA Corn Flakes 500g", .cereal, "corn flakes", 1.10, "500g", "ASDA", true, false, false, "per 100g", 0.22, ["cereal"]),
                p("ASDA Mature Cheddar 400g", .cheese, "cheddar", 2.65, "400g", "ASDA", true, false, false, "per 100g", 0.6625, ["cheese", "cheddar"])
            ],
            "Morrisons": [
                p("Morrisons Semi Skimmed Milk 2L", .milk, "semi-skimmed", 1.58, "2L", "Morrisons", true, false, false, "per litre", 0.79, ["milk"]),
                p("Morrisons Whole Milk 2L", .milk, "whole", 1.62, "2L", "Morrisons", true, false, false, "per litre", 0.81, ["milk"]),
                p("Morrisons White Bread 800g", .bread, "white sliced", 0.82, "800g", "Morrisons", true, false, false, "per 100g", 0.103, ["bread"]),
                p("Morrisons Eggs 12", .eggs, "mixed weight", 2.05, "12 pack", "Morrisons", true, false, false, "per egg", 0.171, ["eggs"]),
                p("Morrisons Salted Butter 250g", .butter, "salted", 1.95, "250g", "Morrisons", true, false, false, "per 100g", 0.78, ["butter"]),
                p("Morrisons Fusilli Pasta 500g", .pasta, "fusilli", 0.88, "500g", "Morrisons", true, false, false, "per 100g", 0.176, ["pasta"]),
                p("Morrisons Baked Beans 4x420g", .bakedBeans, "tinned", 2.05, "4 pack", "Morrisons", true, false, false, "per can", 0.5125, ["beans"]),
                p("Morrisons Bananas", .bananas, "produce", 1.02, "5 pack", "Morrisons", true, false, false, "per banana", 0.204, ["bananas"]),
                p("Morrisons Chicken Breast", .chickenBreast, "fresh", 4.30, "550g", "Morrisons", true, false, false, "per 100g", 0.781, ["chicken breast"]),
                p("Morrisons Muesli 750g", .cereal, "muesli", 1.75, "750g", "Morrisons", true, false, false, "per 100g", 0.233, ["cereal", "muesli"]),
                p("Morrisons Mature Cheddar 400g", .cheese, "cheddar", 2.80, "400g", "Morrisons", true, false, false, "per 100g", 0.70, ["cheese", "cheddar"])
            ],
            "Waitrose": [
                p("Essential Waitrose Semi Skimmed Milk 2L", .milk, "semi-skimmed", 1.80, "2L", "Essential Waitrose", true, false, false, "per litre", 0.90, ["milk"]),
                p("Waitrose Duchy Organic Whole Milk 2L", .milk, "whole", 2.60, "2L", "Duchy", false, true, true, "per litre", 1.30, ["milk", "organic", "premium"]),
                p("Essential Waitrose White Bread 800g", .bread, "white sliced", 1.05, "800g", "Essential Waitrose", true, false, false, "per 100g", 0.131, ["bread"]),
                p("Waitrose Eggs 12", .eggs, "mixed weight", 2.35, "12 pack", "Essential Waitrose", true, false, false, "per egg", 0.195, ["eggs"]),
                p("Waitrose Butter 250g", .butter, "salted", 2.25, "250g", "Essential Waitrose", true, false, false, "per 100g", 0.90, ["butter"]),
                p("Waitrose Spreadable 500g", .butter, "spreadable blend", 2.45, "500g", "Essential Waitrose", true, false, false, "per 100g", 0.49, ["spreadable", "blend"]),
                p("Waitrose Penne Pasta 500g", .pasta, "penne", 1.15, "500g", "Essential Waitrose", true, false, false, "per 100g", 0.23, ["pasta"]),
                p("Waitrose Baked Beans 4x415g", .bakedBeans, "tinned", 2.55, "4 pack", "Essential Waitrose", true, false, false, "per can", 0.6375, ["beans", "baked beans"]),
                p("Waitrose Bananas", .bananas, "produce", 1.25, "5 pack", "Essential Waitrose", true, false, false, "per banana", 0.25, ["banana"]),
                p("Waitrose Chicken Breast Fillets", .chickenBreast, "fresh", 4.95, "550g", "Essential Waitrose", true, false, false, "per 100g", 0.90, ["chicken breast"]),
                p("Waitrose Corn Flakes 500g", .cereal, "corn flakes", 1.65, "500g", "Essential Waitrose", true, false, false, "per 100g", 0.33, ["cereal"]),
                p("Waitrose Mature Cheddar 400g", .cheese, "cheddar", 3.20, "400g", "Essential Waitrose", true, false, false, "per 100g", 0.80, ["cheese", "cheddar"])
            ]
        ]
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
        let market = markets.first { name.hasPrefix($0.name) || brand.contains($0.name) || $0.name == "Waitrose" && name.contains("Waitrose") }?.name ?? "Tesco"
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
