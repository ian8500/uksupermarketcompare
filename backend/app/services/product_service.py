from __future__ import annotations

from app.db import get_connection
from app.services.providers import OpenFoodFactsProvider


def get_product_detail(product_id: str, barcode: str | None = None, *, enrich: bool = True) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
              raw.id AS raw_id,
              raw.source_product_id,
              raw.source_name,
              raw.source_brand,
              raw.source_size,
              raw.source_subcategory,
              raw.image_url,
              raw.category_tags,
              raw.last_updated,
              cp.category,
              cp.canonical_name,
              ps.price,
              ps.promo_price,
              ps.currency,
              ps.unit_description,
              ps.unit_value,
              r.name AS retailer_name,
              r.description AS retailer_description
            FROM raw_retailer_products raw
            JOIN retailers r ON r.id = raw.retailer_id
            JOIN product_mappings pm ON pm.raw_product_id = raw.id
            JOIN canonical_products cp ON cp.id = pm.canonical_product_id
            JOIN (
                SELECT raw_product_id, MAX(captured_at) AS latest_time
                FROM price_snapshots
                GROUP BY raw_product_id
            ) latest ON latest.raw_product_id = raw.id
            JOIN price_snapshots ps ON ps.raw_product_id = raw.id AND ps.captured_at = latest.latest_time
            WHERE CAST(raw.id AS TEXT) = ? OR COALESCE(raw.source_product_id, '') = ?
            LIMIT 1
            """,
            (product_id, product_id),
        ).fetchone()

    if not row:
        return None

    payload = {
        "id": str(row["raw_id"]),
        "retailerProductId": row["source_product_id"],
        "supermarket": row["retailer_name"],
        "supermarketDescription": row["retailer_description"],
        "name": row["source_name"],
        "canonicalName": row["canonical_name"],
        "brand": row["source_brand"],
        "size": row["source_size"],
        "subcategory": row["source_subcategory"],
        "category": row["category"],
        "price": row["price"],
        "promoPrice": row["promo_price"],
        "currency": row["currency"],
        "unitDescription": row["unit_description"],
        "unitValue": row["unit_value"],
        "image": row["image_url"] or None,
        "tags": [tag for tag in (row["category_tags"] or "").split(",") if tag],
        "lastUpdated": row["last_updated"],
    }

    if enrich and barcode:
        payload["enrichment"] = OpenFoodFactsProvider().enrich_barcode(barcode)
    return payload
