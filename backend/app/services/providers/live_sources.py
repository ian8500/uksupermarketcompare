from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.services.providers.base import ProviderProduct

logger = logging.getLogger(__name__)


class LiveSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class TescoLiveSourceConfig:
    mode: str
    base_url: str
    api_key: str | None
    query_terms: list[str]

    @classmethod
    def from_env(cls) -> "TescoLiveSourceConfig":
        query_terms = [q.strip() for q in os.getenv("TESCO_QUERY_TERMS", "milk,bread,eggs,butter").split(",") if q.strip()]
        return cls(
            mode=os.getenv("TESCO_SOURCE_MODE", "structured").strip().lower(),
            base_url=os.getenv("TESCO_SOURCE_BASE_URL", "https://api.trolley.co.uk/api/v1/products").strip(),
            api_key=os.getenv("TESCO_API_KEY"),
            query_terms=query_terms,
        )


class TescoStructuredApiSource:
    """Reads a Tesco-compatible product feed from a structured API.

    This adapter intentionally maps generic fields, so we can swap to official Tesco,
    third-party aggregators, or internal scraped/imported APIs without changing ingestion.
    """

    def __init__(self, config: TescoLiveSourceConfig | None = None) -> None:
        self.config = config or TescoLiveSourceConfig.from_env()

    def fetch_products(self) -> list[ProviderProduct]:
        if not self.config.api_key:
            raise LiveSourceError("TESCO_API_KEY is required for live Tesco structured source mode")

        rows: list[ProviderProduct] = []
        for term in self.config.query_terms:
            rows.extend(self._fetch_for_query(term))

        deduped: dict[str, ProviderProduct] = {}
        for row in rows:
            dedupe_key = row.source_product_id or f"{row.name}|{row.size}|{row.brand}"
            deduped[dedupe_key] = row

        return list(deduped.values())

    def _fetch_for_query(self, term: str) -> list[ProviderProduct]:
        url = f"{self.config.base_url}?query={quote(term)}&retailer=tesco"
        req = Request(
            url,
            headers={
                "User-Agent": "UKSupermarketCompare/1.0",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            },
        )
        try:
            with urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise LiveSourceError(f"Tesco live source HTTP error: {exc.code}") from exc
        except URLError as exc:
            raise LiveSourceError(f"Tesco live source connection error: {exc.reason}") from exc

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
                    last_updated=str(item.get("last_updated") or now),
                )
            )
        logger.info("Tesco live source fetched query=%r rows=%d", term, len(products))
        return products


class OpenFoodFactsProvider:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("OFF_BASE_URL", "https://world.openfoodfacts.org")).rstrip("/")

    def enrich_barcode(self, barcode: str) -> dict:
        url = f"{self.base_url}/api/v2/product/{quote(barcode)}.json"
        req = Request(url, headers={"User-Agent": "UKSupermarketCompare/1.0", "Accept": "application/json"})
        try:
            with urlopen(req, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            logger.warning("OFF enrichment failed barcode=%s error=%s", barcode, exc)
            return {"barcode": barcode, "status": "unavailable"}

        product = payload.get("product") or {}
        return {
            "barcode": barcode,
            "status": "ok" if payload.get("status") == 1 else "not_found",
            "productName": product.get("product_name") or product.get("product_name_en"),
            "brand": product.get("brands"),
            "ingredients": product.get("ingredients_text") or product.get("ingredients_text_en"),
            "allergens": product.get("allergens_hierarchy") or [],
            "nutrition": {
                "energyKcal100g": (product.get("nutriments") or {}).get("energy-kcal_100g"),
                "fat100g": (product.get("nutriments") or {}).get("fat_100g"),
                "saturates100g": (product.get("nutriments") or {}).get("saturated-fat_100g"),
                "carbs100g": (product.get("nutriments") or {}).get("carbohydrates_100g"),
                "sugars100g": (product.get("nutriments") or {}).get("sugars_100g"),
                "protein100g": (product.get("nutriments") or {}).get("proteins_100g"),
                "salt100g": (product.get("nutriments") or {}).get("salt_100g"),
            },
            "image": product.get("image_front_small_url") or product.get("image_url"),
            "source": "openfoodfacts",
            "lastUpdated": datetime.now(UTC).isoformat(),
        }
