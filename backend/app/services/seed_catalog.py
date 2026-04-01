from __future__ import annotations

from decimal import Decimal

from app.models import GroceryCategory

COMMON_KEYWORD_MAP: dict[GroceryCategory, list[str]] = {
    GroceryCategory.milk: ["milk", "semi skimmed", "whole", "skimmed"],
    GroceryCategory.bread: ["bread", "wholemeal", "white", "loaf"],
    GroceryCategory.eggs: ["eggs", "egg", "free range"],
    GroceryCategory.butter: ["butter", "salted", "unsalted", "spread"],
}

SEEDED_SUPERMARKETS: list[dict] = [
    {
        "name": "Tesco",
        "description": "Large UK chain with broad own-brand and branded ranges.",
        "products": [
            {"name": "Tesco Semi Skimmed Milk", "category": GroceryCategory.milk, "subcategory": "semi-skimmed", "price": Decimal("1.55"), "size": "2L", "brand": "Tesco", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per litre", "unitValue": Decimal("0.775"), "tags": ["milk", "semi skimmed", "dairy"]},
            {"name": "Warburtons Medium White Bread", "category": GroceryCategory.bread, "subcategory": "white-sliced", "price": Decimal("1.45"), "size": "800g", "brand": "Warburtons", "isOwnBrand": False, "isPremium": False, "isOrganic": False, "unitDescription": "per loaf", "unitValue": Decimal("1.45"), "tags": ["bread", "bakery", "white"]},
            {"name": "Tesco Free Range Eggs", "category": GroceryCategory.eggs, "subcategory": "free-range", "price": Decimal("2.35"), "size": "12 pack", "brand": "Tesco", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per egg", "unitValue": Decimal("0.196"), "tags": ["eggs", "dairy", "protein"]},
            {"name": "Tesco Salted Butter", "category": GroceryCategory.butter, "subcategory": "salted", "price": Decimal("2.05"), "size": "250g", "brand": "Tesco", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per 100g", "unitValue": Decimal("0.82"), "tags": ["butter", "dairy", "cooking"]},
            {"name": "Tesco Penne Pasta", "category": GroceryCategory.pasta, "subcategory": "dried-pasta", "price": Decimal("0.89"), "size": "500g", "brand": "Tesco", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per 100g", "unitValue": Decimal("0.178"), "tags": ["pasta", "pantry", "italian"]},
        ],
    },
    {
        "name": "ASDA",
        "description": "Value-focused supermarket with extensive essentials range.",
        "products": [
            {"name": "ASDA Whole Milk", "category": GroceryCategory.milk, "subcategory": "whole", "price": Decimal("1.45"), "size": "2L", "brand": "ASDA", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per litre", "unitValue": Decimal("0.725"), "tags": ["milk", "whole", "dairy"]},
            {"name": "ASDA Soft White Bread", "category": GroceryCategory.bread, "subcategory": "white-sliced", "price": Decimal("0.85"), "size": "800g", "brand": "ASDA", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per loaf", "unitValue": Decimal("0.85"), "tags": ["bread", "bakery", "value"]},
            {"name": "ASDA Free Range Eggs", "category": GroceryCategory.eggs, "subcategory": "free-range", "price": Decimal("2.25"), "size": "12 pack", "brand": "ASDA", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per egg", "unitValue": Decimal("0.188"), "tags": ["eggs", "protein", "dairy"]},
            {"name": "ASDA Salted Butter", "category": GroceryCategory.butter, "subcategory": "salted", "price": Decimal("1.99"), "size": "250g", "brand": "ASDA", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per 100g", "unitValue": Decimal("0.796"), "tags": ["butter", "dairy", "cooking"]},
            {"name": "Heinz Baked Beanz", "category": GroceryCategory.bakedBeans, "subcategory": "tinned-beans", "price": Decimal("1.40"), "size": "415g", "brand": "Heinz", "isOwnBrand": False, "isPremium": False, "isOrganic": False, "unitDescription": "per 100g", "unitValue": Decimal("0.337"), "tags": ["baked beans", "pantry", "tin"]},
        ],
    },
    {
        "name": "Sainsbury's",
        "description": "Mainstream UK grocer known for quality own-brand tiers.",
        "products": [
            {"name": "Sainsbury's British Semi Skimmed Milk", "category": GroceryCategory.milk, "subcategory": "semi-skimmed", "price": Decimal("1.60"), "size": "2L", "brand": "Sainsbury's", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per litre", "unitValue": Decimal("0.80"), "tags": ["milk", "semi skimmed", "dairy"]},
            {"name": "Sainsbury's Wholemeal Bread", "category": GroceryCategory.bread, "subcategory": "wholemeal", "price": Decimal("1.20"), "size": "800g", "brand": "Sainsbury's", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per loaf", "unitValue": Decimal("1.20"), "tags": ["bread", "bakery", "wholemeal"]},
            {"name": "Sainsbury's Free Range Eggs", "category": GroceryCategory.eggs, "subcategory": "free-range", "price": Decimal("2.49"), "size": "12 pack", "brand": "Sainsbury's", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per egg", "unitValue": Decimal("0.208"), "tags": ["eggs", "dairy", "protein"]},
            {"name": "Sainsbury's Salted Butter", "category": GroceryCategory.butter, "subcategory": "salted", "price": Decimal("2.15"), "size": "250g", "brand": "Sainsbury's", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per 100g", "unitValue": Decimal("0.86"), "tags": ["butter", "dairy", "cooking"]},
            {"name": "Sainsbury's Mature Cheddar", "category": GroceryCategory.cheese, "subcategory": "cheddar", "price": Decimal("2.65"), "size": "350g", "brand": "Sainsbury's", "isOwnBrand": True, "isPremium": False, "isOrganic": False, "unitDescription": "per 100g", "unitValue": Decimal("0.757"), "tags": ["cheese", "dairy", "sandwich"]},
        ],
    },
]
