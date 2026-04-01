from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.models import GroceryCategory
from app.services.seed_catalog import SEEDED_SUPERMARKETS

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
    supermarkets=[CatalogSupermarket(**market) for market in SEEDED_SUPERMARKETS],
    metadata=CatalogMetadata(
        source="live-backend",
        debugMarker="LIVE_CATALOG_V1",
        generatedAt=datetime.now(UTC).isoformat(),
    ),
)



@router.get('/catalog', response_model=CatalogResponse)
def catalog() -> CatalogResponse:
    return CATALOG.model_copy(
        update={
            "metadata": CatalogMetadata(
                source="live-backend",
                debugMarker="LIVE_CATALOG_V1",
                generatedAt=datetime.now(UTC).isoformat(),
            )
        }
    )
