from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Retailer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    name: str
    description: str


class RawRetailerProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    retailer_id: int
    source_product_id: str | None = None
    source_name: str
    source_brand: str
    source_size: str
    source_subcategory: str
    raw_payload: str | None = None
    searchable_text: str
    created_at: str


class CanonicalProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    canonical_name: str
    intent_key: str
    category: str
    normalized_brand: str
    normalized_unit: str
    normalized_size_value: float | None = None
    tags: str
    searchable_text: str


class ProductMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    raw_product_id: int
    canonical_product_id: int
    confidence: float = 1.0
    method: str = "seed-normalized"


class PriceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    raw_product_id: int
    price: float
    currency: str = "GBP"
    unit_description: str
    unit_value: float
    captured_at: str


class SearchSynonym(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    synonym: str
    canonical_term: str
    term_type: str = "catalog"


class ImportRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    retailer: str
    source_mode: str
    started_at: str
    completed_at: str | None = None
    status: str
    fetched_count: int = 0
    inserted_count: int = 0
    updated_count: int = 0
    mapped_count: int = 0
    unmapped_count: int = 0
    snapshot_count: int = 0
    error_count: int = 0
    error_details: str = "[]"
