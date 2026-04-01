from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from app.models import GroceryCategory
from app.services.normalization import (
    NormalizedSize,
    build_searchable_text,
    infer_category,
    normalize_brand,
    normalize_product_name,
    normalize_size,
    normalize_tags,
    token_fingerprint,
)


@dataclass(frozen=True)
class ProviderProduct:
    source_product_id: str | None
    name: str
    subcategory: str
    price: Decimal
    size: str
    brand: str
    unit_description: str
    unit_value: Decimal
    tags: list[str]
    promo_price: Decimal | None = None
    image_url: str | None = None
    availability: str | None = None
    source_metadata: dict[str, Any] | None = None
    last_updated: str | None = None


@dataclass(frozen=True)
class NormalizedProviderProduct:
    raw: ProviderProduct
    retailer_name: str
    normalized_name: str
    normalized_brand: str
    normalized_tags: list[str]
    normalized_size: NormalizedSize
    category: GroceryCategory
    searchable_text: str
    intent_key: str
    canonical_aliases: list[str]
    token_fingerprint: str


class SupermarketPriceProvider(Protocol):
    name: str
    description: str

    def load_products(self) -> list[ProviderProduct]: ...

    def normalize_products(self) -> list[NormalizedProviderProduct]: ...


class ProductMetadataEnrichmentProvider(Protocol):
    provider_name: str

    def enrich_barcode(self, barcode: str) -> dict[str, Any]: ...


class SeedFileProvider:
    def __init__(self, file_path: Path) -> None:
        payload = json.loads(file_path.read_text())
        self.name = payload["name"]
        self.description = payload["description"]
        self._payload_products = payload["products"]

    def load_products(self) -> list[ProviderProduct]:
        return [
            ProviderProduct(
                source_product_id=item.get("sourceProductId"),
                name=item["name"],
                subcategory=item["subcategory"],
                price=Decimal(str(item["price"])),
                size=item["size"],
                brand=item["brand"],
                unit_description=item["unitDescription"],
                unit_value=Decimal(str(item["unitValue"])),
                tags=item["tags"],
                promo_price=Decimal(str(item["promoPrice"])) if item.get("promoPrice") is not None else None,
                image_url=item.get("imageUrl"),
                availability=item.get("availability"),
                source_metadata=item.get("sourceMetadata") or {"source": "seed"},
                last_updated=item.get("lastUpdated"),
            )
            for item in self._payload_products
        ]

    def normalize_products(self) -> list[NormalizedProviderProduct]:
        normalized_rows: list[NormalizedProviderProduct] = []
        for product in self.load_products():
            normalized_name = normalize_product_name(product.name)
            normalized_brand = normalize_brand(product.brand)
            normalized_tags = normalize_tags(product.tags)
            normalized_size = normalize_size(product.size)
            category = infer_category(product.name, product.tags)
            searchable_text = build_searchable_text(product.name, product.brand, product.size, product.tags)
            intent_key = (
                f"{category.value}:{normalized_name}:{normalized_size.normalized_value or ''}"
                f"{normalized_size.normalized_unit or ''}"
            )
            canonical_aliases = sorted(
                set(
                    [
                        normalized_name,
                        normalize_product_name(product.brand),
                        normalize_product_name(product.subcategory),
                    ]
                )
            )
            normalized_rows.append(
                NormalizedProviderProduct(
                    raw=product,
                    retailer_name=self.name,
                    normalized_name=normalized_name,
                    normalized_brand=normalized_brand,
                    normalized_tags=normalized_tags,
                    normalized_size=normalized_size,
                    category=category,
                    searchable_text=searchable_text,
                    intent_key=intent_key,
                    canonical_aliases=canonical_aliases,
                    token_fingerprint=token_fingerprint(product.name, product.brand, product.size, " ".join(product.tags)),
                )
            )

        return normalized_rows
