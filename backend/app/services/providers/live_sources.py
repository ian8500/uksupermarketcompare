from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.services.providers.base import ProductMetadataEnrichmentProvider, ProviderProduct

logger = logging.getLogger(__name__)


class LiveSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class TescoLiveSourceConfig:
    mode: str
    official_base_url: str
    official_api_key: str | None
    official_partner_id: str | None
    third_party_base_url: str
    third_party_api_key: str | None
    query_terms: list[str]

    @classmethod
    def from_env(cls) -> "TescoLiveSourceConfig":
        query_terms = [q.strip() for q in os.getenv("TESCO_QUERY_TERMS", "milk,bread,eggs,butter").split(",") if q.strip()]
        return cls(
            mode=os.getenv("TESCO_SOURCE_MODE", "auto").strip().lower(),
            official_base_url=os.getenv("TESCO_OFFICIAL_BASE_URL", "").strip(),
            official_api_key=os.getenv("TESCO_OFFICIAL_API_KEY"),
            official_partner_id=os.getenv("TESCO_OFFICIAL_PARTNER_ID"),
            third_party_base_url=os.getenv("TESCO_THIRD_PARTY_BASE_URL", "https://api.trolley.co.uk/api/v1/products").strip(),
            third_party_api_key=os.getenv("TESCO_THIRD_PARTY_API_KEY") or os.getenv("TESCO_API_KEY"),
            query_terms=query_terms,
        )


class TescoUpstreamSource(Protocol):
    source_name: str

    def is_configured(self) -> bool: ...

    def fetch_products(self) -> list[ProviderProduct]: ...


class TescoOfficialApiSource:
    source_name = "official"

    def __init__(self, config: TescoLiveSourceConfig) -> None:
        self.config = config

    def is_configured(self) -> bool:
        return bool(self.config.official_base_url and self.config.official_api_key and self.config.official_partner_id)

    def fetch_products(self) -> list[ProviderProduct]:
        if not self.is_configured():
            raise LiveSourceError("Official Tesco source is not configured")
        return _fetch_structured_products(
            base_url=self.config.official_base_url,
            api_key=self.config.official_api_key,
            query_terms=self.config.query_terms,
            source_name=self.source_name,
            extra_headers={"X-Partner-Id": str(self.config.official_partner_id)},
        )


class TescoThirdPartyApiSource:
    source_name = "third_party"

    def __init__(self, config: TescoLiveSourceConfig) -> None:
        self.config = config

    def is_configured(self) -> bool:
        return bool(self.config.third_party_base_url and self.config.third_party_api_key)

    def fetch_products(self) -> list[ProviderProduct]:
        if not self.is_configured():
            raise LiveSourceError("Third-party Tesco source is not configured")
        return _fetch_structured_products(
            base_url=self.config.third_party_base_url,
            api_key=self.config.third_party_api_key,
            query_terms=self.config.query_terms,
            source_name=self.source_name,
        )


class OpenFoodFactsProvider(ProductMetadataEnrichmentProvider):
    provider_name = "openfoodfacts"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("OFF_BASE_URL", "https://world.openfoodfacts.org")).rstrip("/")

    def enrich_barcode(self, barcode: str) -> dict:
        url = f"{self.base_url}/api/v2/product/{quote(barcode)}.json"
        req = Request(url, headers={"User-Agent": "UKSupermarketCompare/1.0", "Accept": "application/json"})
        try:
            with urlopen(req, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            logger.warning("OFF enrichment unavailable barcode=%s error=%s", barcode, exc)
            return {"barcode": barcode, "status": "unavailable", "source": self.provider_name}

        product = payload.get("product") or {}
        nutriments = product.get("nutriments") or {}
        return {
            "barcode": barcode,
            "status": "ok" if payload.get("status") == 1 else "not_found",
            "productName": product.get("product_name") or product.get("product_name_en"),
            "brand": product.get("brands"),
            "ingredients": product.get("ingredients_text") or product.get("ingredients_text_en"),
            "allergens": product.get("allergens_hierarchy") or [],
            "packaging": product.get("packaging") or product.get("packaging_text_en"),
            "nutrition": {
                "energyKcal100g": nutriments.get("energy-kcal_100g"),
                "fat100g": nutriments.get("fat_100g"),
                "saturates100g": nutriments.get("saturated-fat_100g"),
                "carbs100g": nutriments.get("carbohydrates_100g"),
                "sugars100g": nutriments.get("sugars_100g"),
                "protein100g": nutriments.get("proteins_100g"),
                "salt100g": nutriments.get("salt_100g"),
            },
            "image": product.get("image_front_small_url") or product.get("image_url"),
            "source": self.provider_name,
            "lastUpdated": datetime.now(UTC).isoformat(),
        }


def _fetch_structured_products(
    *,
    base_url: str,
    api_key: str | None,
    query_terms: list[str],
    source_name: str,
    extra_headers: dict[str, str] | None = None,
) -> list[ProviderProduct]:
    if not api_key:
        raise LiveSourceError("API key is required")

    rows: list[ProviderProduct] = []
    for term in query_terms:
        rows.extend(_fetch_for_query(base_url, api_key, term, source_name, extra_headers or {}))

    deduped: dict[str, ProviderProduct] = {}
    for row in rows:
        dedupe_key = row.source_product_id or f"{row.name}|{row.size}|{row.brand}"
        deduped[dedupe_key] = row

    return list(deduped.values())


def _fetch_for_query(base_url: str, api_key: str, term: str, source_name: str, extra_headers: dict[str, str]) -> list[ProviderProduct]:
    url = f"{base_url}?query={quote(term)}&retailer=tesco"
    headers = {
        "User-Agent": "UKSupermarketCompare/1.0",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    headers.update(extra_headers)
    req = Request(url, headers=headers)

    try:
        with urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise LiveSourceError(f"Tesco {source_name} source HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise LiveSourceError(f"Tesco {source_name} source connection error: {exc.reason}") from exc

    items = payload.get("products") or payload.get("items") or []
    now = datetime.now(UTC).isoformat()
    products: list[ProviderProduct] = []
    for item in items:
        price_value = item.get("price") or item.get("current_price")
        if price_value in (None, ""):
            continue
        unit_value = item.get("unit_price") or item.get("unit_value") or 0
        tags = item.get("tags") or item.get("category_tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        products.append(
            ProviderProduct(
                source_product_id=str(item.get("id") or item.get("product_id") or "") or None,
                name=str(item.get("name") or item.get("title") or "Unknown Tesco item"),
                subcategory=str(item.get("subcategory") or item.get("category") or "Groceries"),
                price=Decimal(str(price_value)),
                size=str(item.get("size") or item.get("package_size") or "1 item"),
                brand=str(item.get("brand") or "Tesco"),
                unit_description=str(item.get("unit_description") or "per item"),
                unit_value=Decimal(str(unit_value or 0)),
                tags=[str(tag) for tag in tags],
                promo_price=Decimal(str(item.get("promo_price"))) if item.get("promo_price") not in (None, "") else None,
                image_url=item.get("image") or item.get("image_url"),
                availability=item.get("availability"),
                source_metadata={"upstream": source_name, "raw_id": item.get("id")},
                last_updated=str(item.get("last_updated") or now),
            )
        )
    logger.info("Tesco upstream fetch source=%s query=%r rows=%d", source_name, term, len(products))
    return products
