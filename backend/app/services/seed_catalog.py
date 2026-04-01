from __future__ import annotations

from app.models import GroceryCategory
from app.services.normalization import normalize_brand
from app.services.providers import AsdaProvider, SainsburysProvider, TescoProvider

COMMON_KEYWORD_MAP: dict[GroceryCategory, list[str]] = {
    GroceryCategory.milk: ["milk", "semi skimmed", "whole", "skimmed", "dairy"],
    GroceryCategory.bread: ["bread", "loaf", "wholemeal", "white", "toastie"],
    GroceryCategory.eggs: ["egg", "eggs", "free range", "dozen"],
    GroceryCategory.butter: ["butter", "spread", "salted", "unsalted"],
    GroceryCategory.pasta: ["pasta", "penne", "spaghetti", "fusilli"],
    GroceryCategory.bakedBeans: ["baked beans", "beans", "beanz", "tin"],
    GroceryCategory.bananas: ["banana", "bananas", "fruit"],
    GroceryCategory.chickenBreast: ["chicken breast", "chicken", "fillet", "protein"],
    GroceryCategory.cereal: ["cereal", "corn flakes", "wheat biscuits", "granola"],
    GroceryCategory.cheese: ["cheese", "cheddar", "mozzarella", "red leicester"],
    GroceryCategory.tomatoes: ["tomato", "tomatoes", "plum", "salad"],
    GroceryCategory.rice: ["rice", "basmati", "long grain", "microwave"],
    GroceryCategory.yogurt: ["yogurt", "yoghurt", "greek", "dairy"],
    GroceryCategory.apples: ["apple", "apples", "fruit", "gala"],
}


def _seed_market(provider):
    return {
        "name": provider.name,
        "description": provider.description,
        "products": [
            {
                "name": row.raw.name,
                "category": row.category,
                "subcategory": row.raw.subcategory,
                "price": row.raw.price,
                "size": row.raw.size,
                "brand": row.raw.brand,
                "isOwnBrand": row.normalized_brand == normalize_brand(provider.name),
                "isPremium": "premium" in row.searchable_text or "organic" in row.searchable_text,
                "isOrganic": "organic" in row.searchable_text,
                "unitDescription": row.raw.unit_description,
                "unitValue": row.raw.unit_value,
                "tags": row.raw.tags,
            }
            for row in provider.normalize_products()
        ],
    }


SEEDED_SUPERMARKETS: list[dict] = [_seed_market(TescoProvider()), _seed_market(AsdaProvider()), _seed_market(SainsburysProvider())]
