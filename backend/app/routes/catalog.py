from decimal import Decimal
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.services.seed_catalog import SEEDED_SUPERMARKETS

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
            name=market["name"],
            description=market["description"],
            products=[
                CatalogProduct(
                    **{**product, "category": product["category"].value},
                )
                for product in market["products"]
            ],
        )
        for market in SEEDED_SUPERMARKETS
    ],
    metadata=CatalogMetadata(
        source="backend.catalog",
        debugMarker="LIVE_CATALOG_V3_MATCHING_INTELLIGENCE",
        generatedAt="2026-04-01T00:00:00Z",
    ),
)


@router.get('/catalog', response_model=CatalogResponse)
def catalog() -> CatalogResponse:
    return CATALOG
