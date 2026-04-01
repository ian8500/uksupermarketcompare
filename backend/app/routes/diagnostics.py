from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.services.diagnostics import catalog_diagnostics, search_diagnostics

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


class ProductsPerSupermarket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supermarket: str
    products: int


class CatalogDiagnosticsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    productsPerSupermarket: list[ProductsPerSupermarket]
    canonicalProducts: int
    mappings: int
    categoriesCovered: list[str]
    priceSnapshots: int
    priceDropAlertCandidates: int


class EndpointSearchDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint: str
    totalQueries: int
    missQueries: int


class SearchDiagnosticsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    totalQueries: int
    missQueries: int
    missRate: float
    weakMatches: int
    avgTopScore: float
    byEndpoint: list[EndpointSearchDiagnostics]


@router.get("/catalog", response_model=CatalogDiagnosticsResponse)
def catalog_metrics() -> CatalogDiagnosticsResponse:
    return CatalogDiagnosticsResponse(**catalog_diagnostics())


@router.get("/search", response_model=SearchDiagnosticsResponse)
def search_metrics() -> SearchDiagnosticsResponse:
    return SearchDiagnosticsResponse(**search_diagnostics())
