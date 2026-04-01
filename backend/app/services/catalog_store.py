from __future__ import annotations

from decimal import Decimal

from app.db import get_connection
from app.models import GroceryCategory
from app.services.ingestion import import_catalog_data
from app.services.normalization import normalize_brand


def ensure_seed_data() -> None:
    with get_connection() as conn:
        retailer_count = conn.execute("SELECT COUNT(*) FROM retailers").fetchone()[0]
    if retailer_count > 0:
        return
    import_catalog_data()


def load_catalog_rows() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
              r.name AS retailer_name,
              r.description AS retailer_description,
              raw.source_name,
              raw.source_brand,
              raw.source_size,
              raw.source_subcategory,
              cp.category,
              cp.tags,
              cp.searchable_text,
              ps.price,
              ps.unit_description,
              ps.unit_value
            FROM retailers r
            JOIN raw_retailer_products raw ON raw.retailer_id = r.id
            JOIN product_mappings pm ON pm.raw_product_id = raw.id
            JOIN canonical_products cp ON cp.id = pm.canonical_product_id
            JOIN (
                SELECT raw_product_id, MAX(captured_at) AS latest_time
                FROM price_snapshots
                GROUP BY raw_product_id
            ) latest ON latest.raw_product_id = raw.id
            JOIN price_snapshots ps ON ps.raw_product_id = raw.id AND ps.captured_at = latest.latest_time
            ORDER BY r.name, raw.source_name
            """
        ).fetchall()

    by_market: dict[str, dict] = {}
    for row in rows:
        by_market.setdefault(
            row["retailer_name"],
            {"name": row["retailer_name"], "description": row["retailer_description"], "products": []},
        )
        category_value = row["category"] if row["category"] in GroceryCategory._value2member_map_ else GroceryCategory.unknown.value
        by_market[row["retailer_name"]]["products"].append(
            {
                "name": row["source_name"],
                "category": GroceryCategory(category_value),
                "subcategory": row["source_subcategory"],
                "price": Decimal(str(row["price"])),
                "size": row["source_size"],
                "brand": row["source_brand"],
                "isOwnBrand": normalize_brand(row["source_brand"]) == normalize_brand(row["retailer_name"]),
                "isPremium": "premium" in row["searchable_text"] or "organic" in row["searchable_text"],
                "isOrganic": "organic" in row["searchable_text"],
                "unitDescription": row["unit_description"],
                "unitValue": Decimal(str(row["unit_value"])),
                "tags": [tag for tag in row["tags"].split(",") if tag],
            }
        )
    return list(by_market.values())
