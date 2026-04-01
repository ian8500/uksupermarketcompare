from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.models import GroceryCategory

router = APIRouter()


class CatalogProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: GroceryCategory
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


class CatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supermarkets: list[CatalogSupermarket]


CATALOG = CatalogResponse(
    supermarkets=[
        CatalogSupermarket(
            name="Tesco",
            description="Large UK chain with broad own-brand and branded ranges.",
            products=[
                CatalogProduct(name="Tesco Semi Skimmed Milk", category=GroceryCategory.milk, subcategory="semi-skimmed", price=Decimal("1.55"), size="2L", brand="Tesco", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per litre", unitValue=Decimal("0.775"), tags=["milk", "semi skimmed", "dairy"]),
                CatalogProduct(name="Warburtons Medium White Bread", category=GroceryCategory.bread, subcategory="white-sliced", price=Decimal("1.45"), size="800g", brand="Warburtons", isOwnBrand=False, isPremium=False, isOrganic=False, unitDescription="per loaf", unitValue=Decimal("1.45"), tags=["bread", "bakery", "white"]),
                CatalogProduct(name="Tesco Free Range Eggs", category=GroceryCategory.eggs, subcategory="free-range", price=Decimal("2.35"), size="12 pack", brand="Tesco", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per egg", unitValue=Decimal("0.196"), tags=["eggs", "dairy", "protein"]),
                CatalogProduct(name="Tesco Penne Pasta", category=GroceryCategory.pasta, subcategory="dried-pasta", price=Decimal("0.89"), size="500g", brand="Tesco", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.178"), tags=["pasta", "pantry", "italian"]),
                CatalogProduct(name="Tesco Chopped Tomatoes", category=GroceryCategory.tomatoes, subcategory="tinned", price=Decimal("0.62"), size="400g", brand="Tesco", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.155"), tags=["tomatoes", "pantry", "cooking"]),
                CatalogProduct(name="Tesco British Chicken Breast Fillets", category=GroceryCategory.chickenBreast, subcategory="fresh", price=Decimal("5.50"), size="650g", brand="Tesco", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per kg", unitValue=Decimal("8.462"), tags=["chicken", "meat", "protein"]),
            ],
        ),
        CatalogSupermarket(
            name="ASDA",
            description="Value-focused supermarket with extensive essentials range.",
            products=[
                CatalogProduct(name="ASDA Whole Milk", category=GroceryCategory.milk, subcategory="whole", price=Decimal("1.45"), size="2L", brand="ASDA", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per litre", unitValue=Decimal("0.725"), tags=["milk", "whole", "dairy"]),
                CatalogProduct(name="ASDA Soft White Bread", category=GroceryCategory.bread, subcategory="white-sliced", price=Decimal("0.85"), size="800g", brand="ASDA", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per loaf", unitValue=Decimal("0.85"), tags=["bread", "bakery", "value"]),
                CatalogProduct(name="Heinz Baked Beanz", category=GroceryCategory.bakedBeans, subcategory="tinned-beans", price=Decimal("1.40"), size="415g", brand="Heinz", isOwnBrand=False, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.337"), tags=["baked beans", "pantry", "tin"]),
                CatalogProduct(name="ASDA Easy Cook Long Grain Rice", category=GroceryCategory.rice, subcategory="dried-rice", price=Decimal("1.35"), size="1kg", brand="ASDA", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.135"), tags=["rice", "pantry", "staple"]),
                CatalogProduct(name="ASDA Ripe & Ready Bananas", category=GroceryCategory.bananas, subcategory="fresh-fruit", price=Decimal("0.82"), size="5 pack", brand="ASDA", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per banana", unitValue=Decimal("0.164"), tags=["bananas", "fruit & veg", "fresh"]),
                CatalogProduct(name="ASDA Greek Style Yogurt", category=GroceryCategory.yogurt, subcategory="greek-style", price=Decimal("1.25"), size="500g", brand="ASDA", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.25"), tags=["yogurt", "dairy", "breakfast"]),
            ],
        ),
        CatalogSupermarket(
            name="Sainsbury's",
            description="Mainstream UK grocer known for quality own-brand tiers.",
            products=[
                CatalogProduct(name="Sainsbury's Salted Butter", category=GroceryCategory.butter, subcategory="salted", price=Decimal("2.15"), size="250g", brand="Sainsbury's", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.86"), tags=["butter", "dairy", "cooking"]),
                CatalogProduct(name="Sainsbury's British Apples", category=GroceryCategory.apples, subcategory="fresh-fruit", price=Decimal("1.95"), size="6 pack", brand="Sainsbury's", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per apple", unitValue=Decimal("0.325"), tags=["apples", "fruit & veg", "fresh"]),
                CatalogProduct(name="Sainsbury's Mature Cheddar", category=GroceryCategory.cheese, subcategory="cheddar", price=Decimal("2.65"), size="350g", brand="Sainsbury's", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.757"), tags=["cheese", "dairy", "sandwich"]),
                CatalogProduct(name="Kellogg's Corn Flakes", category=GroceryCategory.cereal, subcategory="corn-flakes", price=Decimal("3.10"), size="500g", brand="Kellogg's", isOwnBrand=False, isPremium=False, isOrganic=False, unitDescription="per 100g", unitValue=Decimal("0.62"), tags=["cereal", "breakfast", "pantry"]),
                CatalogProduct(name="Sainsbury's Organic Vine Tomatoes", category=GroceryCategory.tomatoes, subcategory="fresh", price=Decimal("1.95"), size="330g", brand="Sainsbury's", isOwnBrand=True, isPremium=True, isOrganic=True, unitDescription="per 100g", unitValue=Decimal("0.591"), tags=["tomatoes", "fruit & veg", "organic"]),
                CatalogProduct(name="Sainsbury's British Chicken Breast", category=GroceryCategory.chickenBreast, subcategory="fresh", price=Decimal("5.95"), size="650g", brand="Sainsbury's", isOwnBrand=True, isPremium=False, isOrganic=False, unitDescription="per kg", unitValue=Decimal("9.154"), tags=["chicken", "meat", "fresh"]),
            ],
        ),
    ]
)


@router.get('/catalog', response_model=CatalogResponse)
def catalog() -> CatalogResponse:
    return CATALOG
