from __future__ import annotations

import json
import logging
import os
import socket
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol
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
    timeout_seconds: int
    max_retries: int

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
            timeout_seconds=max(5, int(os.getenv("TESCO_SOURCE_TIMEOUT_SECONDS", "20"))),
            max_retries=max(0, int(os.getenv("TESCO_SOURCE_MAX_RETRIES", "1"))),
        )


class TescoUpstreamSource(Protocol):
    source_name: str
    last_fetch_report: dict[str, Any]

    def is_configured(self) -> bool: ...

    def fetch_products(self) -> list[ProviderProduct]: ...


class TescoOfficialApiSource:
    source_name = "official"

    def __init__(self, config: TescoLiveSourceConfig) -> None:
        self.config = config
        self.last_fetch_report: dict[str, Any] = {}

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
            timeout_seconds=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
            report_target=self,
        )


class TescoThirdPartyApiSource:
    source_name = "third_party"

    def __init__(self, config: TescoLiveSourceConfig) -> None:
        self.config = config
        self.last_fetch_report: dict[str, Any] = {}

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
            timeout_seconds=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
            report_target=self,
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
    timeout_seconds: int = 20,
    max_retries: int = 1,
    report_target: TescoUpstreamSource | None = None,
) -> list[ProviderProduct]:
    if not api_key:
        raise LiveSourceError("API key is required")

    rows: list[ProviderProduct] = []
    failures: list[str] = []
    fetched = 0
    skipped = 0
    rejected = 0
    mapped = 0

    for term in query_terms:
        try:
            query_rows, query_report = _fetch_for_query(
                base_url=base_url,
                api_key=api_key,
                term=term,
                source_name=source_name,
                extra_headers=extra_headers or {},
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
            )
            rows.extend(query_rows)
            fetched += query_report["fetched"]
            skipped += query_report["skipped"]
            rejected += query_report["rejected"]
            mapped += query_report["mapped"]
        except LiveSourceError as exc:
            failures.append(f"{term}:{exc}")
            logger.warning("Tesco upstream query failed source=%s query=%r error=%s", source_name, term, exc)

    deduped: dict[str, ProviderProduct] = {}
    for row in rows:
        dedupe_key = row.source_product_id or f"{row.name}|{row.size}|{row.brand}"
        deduped[dedupe_key] = row

    if not deduped and failures:
        raise LiveSourceError(f"All Tesco upstream queries failed source={source_name}")
    if failures:
        logger.warning(
            "Tesco upstream partial failure source=%s failed_queries=%d total_queries=%d",
            source_name,
            len(failures),
            len(query_terms),
        )

    report = {
        "source": source_name,
        "fetched": fetched,
        "skipped": skipped,
        "rejected": rejected,
        "mapped": mapped,
        "deduped": len(deduped),
        "failed_queries": len(failures),
        "total_queries": len(query_terms),
    }
    if report_target is not None:
        report_target.last_fetch_report = report

    logger.info(
        "Tesco upstream summary source=%s fetched=%d skipped=%d rejected=%d mapped=%d deduped=%d failed_queries=%d total_queries=%d",
        source_name,
        fetched,
        skipped,
        rejected,
        mapped,
        len(deduped),
        len(failures),
        len(query_terms),
    )
    return list(deduped.values())


def _fetch_for_query(
    *,
    base_url: str,
    api_key: str,
    term: str,
    source_name: str,
    extra_headers: dict[str, str],
    timeout_seconds: int,
    max_retries: int,
) -> tuple[list[ProviderProduct], dict[str, int]]:
    url = f"{base_url}?query={quote(term)}&retailer=tesco"
    headers = {
        "User-Agent": "UKSupermarketCompare/1.0",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    headers.update(extra_headers)
    req = Request(url, headers=headers)

    payload = _request_json_with_retries(req, source_name, timeout_seconds, max_retries)
    items = _validated_items(payload, source_name)

    now = datetime.now(UTC).isoformat()
    products: list[ProviderProduct] = []
    skipped = 0
    rejected = 0

    for item in items:
        if not isinstance(item, dict):
            rejected += 1
            continue
        price_value = item.get("price") or item.get("current_price")
        if price_value in (None, ""):
            skipped += 1
            continue
        try:
            parsed_price = Decimal(str(price_value))
        except Exception:
            logger.warning("Tesco upstream skipped malformed price source=%s query=%r", source_name, term)
            rejected += 1
            continue

        unit_value = item.get("unit_price") or item.get("unit_value") or 0
        try:
            parsed_unit_value = Decimal(str(unit_value or 0))
        except Exception:
            parsed_unit_value = Decimal("0")

        tags = item.get("tags") or item.get("category_tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        promo_price_raw = item.get("promo_price")
        promo_price = None
        if promo_price_raw not in (None, ""):
            try:
                promo_price = Decimal(str(promo_price_raw))
            except Exception:
                promo_price = None

        products.append(
            ProviderProduct(
                source_product_id=str(item.get("id") or item.get("product_id") or "") or None,
                name=str(item.get("name") or item.get("title") or "Unknown Tesco item"),
                subcategory=str(item.get("subcategory") or item.get("category") or "Groceries"),
                price=parsed_price,
                size=str(item.get("size") or item.get("package_size") or "1 item"),
                brand=str(item.get("brand") or "Tesco"),
                unit_description=str(item.get("unit_description") or "per item"),
                unit_value=parsed_unit_value,
                tags=[str(tag) for tag in tags],
                promo_price=promo_price,
                image_url=item.get("image") or item.get("image_url"),
                availability=item.get("availability"),
                source_metadata={"upstream": source_name, "raw_id": item.get("id")},
                last_updated=str(item.get("last_updated") or now),
            )
        )

    logger.info(
        "Tesco upstream fetch source=%s query=%r fetched=%d skipped=%d rejected=%d mapped=%d",
        source_name,
        term,
        len(items),
        skipped,
        rejected,
        len(products),
    )
    return products, {"fetched": len(items), "skipped": skipped, "rejected": rejected, "mapped": len(products)}


def _validated_items(payload: object, source_name: str) -> list[object]:
    if not isinstance(payload, dict):
        raise LiveSourceError(f"Tesco {source_name} source invalid payload root")

    items = payload.get("products")
    if items is None:
        items = payload.get("items")
    if items is None:
        return []
    if not isinstance(items, list):
        raise LiveSourceError(f"Tesco {source_name} source invalid products field")
    return items


def _request_json_with_retries(req: Request, source_name: str, timeout_seconds: int, max_retries: int) -> object:
    attempts = max_retries + 1
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(req, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 429:
                if attempt >= attempts:
                    raise LiveSourceError(f"Tesco {source_name} source rate limited") from exc
                retry_after = _retry_after_seconds(exc)
                logger.warning(
                    "Tesco upstream rate limited source=%s attempt=%d/%d retry_after_seconds=%d",
                    source_name,
                    attempt,
                    attempts,
                    retry_after,
                )
                time.sleep(retry_after)
                continue
            raise LiveSourceError(f"Tesco {source_name} source HTTP error: {exc.code}") from exc
        except TimeoutError as exc:
            raise LiveSourceError(f"Tesco {source_name} source timeout after {timeout_seconds}s") from exc
        except socket.timeout as exc:
            raise LiveSourceError(f"Tesco {source_name} source timeout after {timeout_seconds}s") from exc
        except URLError as exc:
            reason = str(exc.reason).lower()
            if "timed out" in reason:
                raise LiveSourceError(f"Tesco {source_name} source timeout after {timeout_seconds}s") from exc
            raise LiveSourceError(f"Tesco {source_name} source connection error: {exc.reason}") from exc
    raise LiveSourceError(f"Tesco {source_name} source unavailable")


def _retry_after_seconds(exc: HTTPError) -> int:
    raw = exc.headers.get("Retry-After") if exc.headers else None
    if raw and str(raw).isdigit():
        return max(1, min(int(raw), 5))
    return 1
