from decimal import Decimal
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

router = APIRouter()

SwiftGroceryCategory = Literal[
    "milk",
    "bread",
    "eggs",
    "butter",
    "pasta",
    "bakedBeans",
    "bananas",
    "chickenBreast",
    "cereal",
    "cheese",
    "tomatoes",
    "rice",
    "yogurt",
    "apples",
    "unknown",
]


class CatalogProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: SwiftGroceryCategory
    subcategory: str
    price: Decimal
    size: str
    brand: str
    isOwnBrand: bool
    isPremium: bool
    isOrganic: bool
    unitDescription: str
    unitValue: Decimal
    tags: list[str]


class CatalogSupermarket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    products: list[CatalogProduct]


class CatalogMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    debugMarker: str
    generatedAt: str


class CatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supermarkets: list[CatalogSupermarket]
    metadata: CatalogMetadata


CATALOG = CatalogResponse(
    supermarkets=[
        CatalogSupermarket(
            name="Tesco",
            description="Large UK chain with broad own-brand and branded ranges.",
            products=[
                CatalogProduct(name="Tesco British Semi Skimmed Milk", category="milk", subcategory="milk", price=Decimal("1.55"), size="2L", brand="Tesco", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per litre", unitValue=Decimal("0.775"), tags=["milk", "semi skimmed", "daily staple"]),
                CatalogProduct(name="Warburtons Toastie Thick White Bread", category="bread", subcategory="bread", price=Decimal("1.45"), size="800g", brand="Warburtons", isOwnBrand=False, isPremium=False, isOrganic=False, unitDescription="per loaf", unitValue=Decimal("1.45"), tags=["bread", "sliced", "toast"]),
                CatalogProduct(name="Tesco Italian Passata", category="tomatoes", subcategory="cooking sauce", price=Decimal("0.89"), size="500g", brand="Tesco", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.178"), tags=["tomato", "pasta", "cupboard"]),
                CatalogProduct(name="Tesco Ripe & Ready Avocados", category="unknown", subcategory="fresh fruit", price=Decimal("1.99"), size="2 pack", brand="Tesco", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per avocado", unitValue=Decimal("0.995"), tags=["avocado", "fresh", "produce"]),
                CatalogProduct(name="Tesco British Chicken Breast Fillets", category="chickenBreast", subcategory="chicken", price=Decimal("5.50"), size="650g", brand="Tesco", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per kg", unitValue=Decimal("8.46"), tags=["chicken", "protein", "fresh"]),
            ],
        ),
        CatalogSupermarket(
            name="ASDA",
            description="Value-focused supermarket with extensive essentials range.",
            products=[
                CatalogProduct(name="ASDA Whole Milk", category="milk", subcategory="milk", price=Decimal("1.45"), size="2L", brand="ASDA", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per litre", unitValue=Decimal("0.725"), tags=["milk", "whole", "daily staple"]),
                CatalogProduct(name="ASDA Soft White Bread", category="bread", subcategory="bread", price=Decimal("0.85"), size="800g", brand="ASDA", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per loaf", unitValue=Decimal("0.85"), tags=["bread", "value", "sandwich"]),
                CatalogProduct(name="Heinz Baked Beans", category="bakedBeans", subcategory="tinned food", price=Decimal("1.40"), size="415g", brand="Heinz", isOwnBrand=False, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.337"), tags=["beans", "tin", "cupboard"]),
                CatalogProduct(name="ASDA Sweet Clementines", category="unknown", subcategory="fresh fruit", price=Decimal("2.10"), size="600g", brand="ASDA", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.35"), tags=["citrus", "fresh", "produce"]),
                CatalogProduct(name="ASDA 5% Fat Beef Mince", category="unknown", subcategory="beef", price=Decimal("4.75"), size="500g", brand="ASDA", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per kg", unitValue=Decimal("9.50"), tags=["beef", "mince", "protein"]),
            ],
        ),
        CatalogSupermarket(
            name="Sainsbury's",
            description="Mainstream UK grocer known for quality own-brand tiers.",
            products=[
                CatalogProduct(name="Sainsbury's Mature Cheddar", category="cheese", subcategory="cheese", price=Decimal("2.65"), size="350g", brand="Sainsbury's", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.757"), tags=["cheddar", "cheese", "sandwich"]),
                CatalogProduct(name="Sainsbury's Wholemeal Bread", category="bread", subcategory="bread", price=Decimal("1.20"), size="800g", brand="Sainsbury's", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per loaf", unitValue=Decimal("1.20"), tags=["bread", "wholemeal", "bakery"]),
                CatalogProduct(name="Sainsbury's Basmati Rice", category="rice", subcategory="rice", price=Decimal("2.25"), size="1kg", brand="Sainsbury's", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.225"), tags=["rice", "dry goods", "cupboard"]),
                CatalogProduct(name="Sainsbury's Vine Tomatoes", category="tomatoes", subcategory="fresh vegetables", price=Decimal("2.00"), size="300g", brand="Sainsbury's", isOwnBrand=True, isPremium=True, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.667"), tags=["tomatoes", "fresh", "salad"]),
                CatalogProduct(name="Sainsbury's Salmon Fillets", category="unknown", subcategory="fish", price=Decimal("6.00"), size="240g", brand="Sainsbury's", isOwnBrand=True, isPremium=True, isOrganic=False, unitDescription="per kg", unitValue=Decimal("25.00"), tags=["salmon", "fish", "protein"]),
            ],
        ),
    ],
    metadata=CatalogMetadata(
        source="backend.catalog",
        debugMarker="LIVE_CATALOG_V2_SWIFT_CATEGORY_MATCH",
        generatedAt="2026-04-01T00:00:00Z",
    ),
)


@router.get('/catalog', response_model=CatalogResponse)
def catalog() -> CatalogResponse:
    return CATALOG
