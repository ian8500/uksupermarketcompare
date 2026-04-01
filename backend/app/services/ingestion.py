from __future__ import annotations

from datetime import UTC, datetime
import logging

from app.db import get_connection
from app.services.providers import AsdaProvider, CatalogProvider, SainsburysProvider, TescoProvider

DEFAULT_SYNONYMS: dict[str, str] = {
    "beanz": "baked beans",
    "yoghurt": "yogurt",
    "loaf": "bread",
    "fillets": "fillet",
}
logger = logging.getLogger(__name__)


def default_providers() -> list[CatalogProvider]:
    return [TescoProvider(), AsdaProvider(), SainsburysProvider()]


def import_catalog_data(providers: list[CatalogProvider] | None = None, *, replace_existing: bool = False) -> dict[str, int]:
    providers = providers or default_providers()
    inserted_raw = 0
    updated_raw = 0
    inserted_canonical = 0
    inserted_price_snapshots = 0

    with get_connection() as conn:
        for provider in providers:
            logger.info("Starting import for provider=%s replace_existing=%s", provider.name, replace_existing)
            retailer_row = conn.execute("SELECT id FROM retailers WHERE name = ?", (provider.name,)).fetchone()
            if retailer_row:
                retailer_id = retailer_row[0]
                conn.execute("UPDATE retailers SET description = ? WHERE id = ?", (provider.description, retailer_id))
            else:
                retailer_id = conn.execute(
                    "INSERT INTO retailers(name, description) VALUES(?, ?)", (provider.name, provider.description)
                ).lastrowid

            if replace_existing:
                conn.execute(
                    "DELETE FROM price_snapshots WHERE raw_product_id IN (SELECT id FROM raw_retailer_products WHERE retailer_id = ?)",
                    (retailer_id,),
                )
                conn.execute(
                    "DELETE FROM product_mappings WHERE raw_product_id IN (SELECT id FROM raw_retailer_products WHERE retailer_id = ?)",
                    (retailer_id,),
                )
                conn.execute("DELETE FROM raw_retailer_products WHERE retailer_id = ?", (retailer_id,))

            for product in provider.normalize_products():
                canonical_row = conn.execute(
                    "SELECT id FROM canonical_products WHERE intent_key = ?", (product.intent_key,)
                ).fetchone()
                if canonical_row:
                    canonical_id = canonical_row[0]
                else:
                    canonical_id = conn.execute(
                        """
                        INSERT INTO canonical_products(
                            canonical_name, intent_key, category, normalized_brand,
                            normalized_unit, normalized_size_value, tags, searchable_text
                        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            product.normalized_name,
                            product.intent_key,
                            product.category.value,
                            product.normalized_brand,
                            product.normalized_size.normalized_unit or "",
                            product.normalized_size.normalized_value,
                            ",".join(product.normalized_tags),
                            product.searchable_text,
                        ),
                    ).lastrowid
                    inserted_canonical += 1

                raw_row = conn.execute(
                    """
                    SELECT id FROM raw_retailer_products
                    WHERE retailer_id = ?
                    AND COALESCE(source_product_id, '') = COALESCE(?, '')
                    AND source_name = ? AND source_brand = ? AND source_size = ?
                    """,
                    (
                        retailer_id,
                        product.raw.source_product_id,
                        product.raw.name,
                        product.raw.brand,
                        product.raw.size,
                    ),
                ).fetchone()

                now = datetime.now(UTC).isoformat()
                if raw_row:
                    raw_product_id = raw_row[0]
                    conn.execute(
                        """
                        UPDATE raw_retailer_products
                        SET source_subcategory = ?, searchable_text = ?, created_at = ?
                        WHERE id = ?
                        """,
                        (product.raw.subcategory, product.searchable_text, now, raw_product_id),
                    )
                    updated_raw += 1
                else:
                    raw_product_id = conn.execute(
                        """
                        INSERT INTO raw_retailer_products(
                            retailer_id, source_product_id, source_name, source_brand, source_size, source_subcategory,
                            searchable_text, created_at
                        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            retailer_id,
                            product.raw.source_product_id,
                            product.raw.name,
                            product.raw.brand,
                            product.raw.size,
                            product.raw.subcategory,
                            product.searchable_text,
                            now,
                        ),
                    ).lastrowid
                    inserted_raw += 1

                conn.execute(
                    """
                    INSERT INTO product_mappings(raw_product_id, canonical_product_id, confidence, method)
                    VALUES(?, ?, ?, ?)
                    ON CONFLICT(raw_product_id) DO UPDATE SET
                        canonical_product_id = excluded.canonical_product_id,
                        confidence = excluded.confidence,
                        method = excluded.method
                    """,
                    (raw_product_id, canonical_id, 1.0, f"{provider.name.lower()}-normalized"),
                )

                latest = conn.execute(
                    """
                    SELECT price, unit_value FROM price_snapshots
                    WHERE raw_product_id = ?
                    ORDER BY captured_at DESC LIMIT 1
                    """,
                    (raw_product_id,),
                ).fetchone()
                new_price = float(product.raw.price)
                new_unit_value = float(product.raw.unit_value)
                if not latest or latest["price"] != new_price or latest["unit_value"] != new_unit_value:
                    conn.execute(
                        """
                        INSERT INTO price_snapshots(raw_product_id, price, currency, unit_description, unit_value, captured_at)
                        VALUES(?, ?, ?, ?, ?, ?)
                        """,
                        (raw_product_id, new_price, "GBP", product.raw.unit_description, new_unit_value, now),
                    )
                    inserted_price_snapshots += 1
            logger.info(
                "Completed import provider=%s inserted_raw=%d updated_raw=%d inserted_canonical=%d inserted_price_snapshots=%d",
                provider.name,
                inserted_raw,
                updated_raw,
                inserted_canonical,
                inserted_price_snapshots,
            )

        for synonym, canonical in DEFAULT_SYNONYMS.items():
            conn.execute(
                "INSERT OR IGNORE INTO search_synonyms(synonym, canonical_term, term_type) VALUES(?, ?, ?)",
                (synonym, canonical, "catalog"),
            )
        conn.commit()
    logger.info(
        "Import finished providers=%d inserted_raw=%d updated_raw=%d inserted_canonical=%d inserted_price_snapshots=%d",
        len(providers),
        inserted_raw,
        updated_raw,
        inserted_canonical,
        inserted_price_snapshots,
    )

    return {
        "providers": len(providers),
        "inserted_raw": inserted_raw,
        "updated_raw": updated_raw,
        "inserted_canonical": inserted_canonical,
        "inserted_price_snapshots": inserted_price_snapshots,
    }
