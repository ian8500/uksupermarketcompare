from __future__ import annotations

from datetime import datetime, UTC
from decimal import Decimal

from app.db import get_connection
from app.models import GroceryCategory
from app.services.normalization import (
    build_searchable_text,
    infer_category,
    normalize_brand,
    normalize_product_name,
    normalize_size,
    normalize_tags,
)
from app.services.seed_catalog import SEEDED_SUPERMARKETS


def ensure_seed_data() -> None:
    with get_connection() as conn:
        retailer_count = conn.execute("SELECT COUNT(*) FROM retailers").fetchone()[0]
        if retailer_count > 0:
            return

        for market in SEEDED_SUPERMARKETS:
            cur = conn.execute(
                "INSERT INTO retailers(name, description) VALUES(?, ?)",
                (market["name"], market["description"]),
            )
            retailer_id = cur.lastrowid

            for product in market["products"]:
                normalized_name = normalize_product_name(product["name"])
                normalized_brand = normalize_brand(product["brand"])
                normalized_tags = normalize_tags(product["tags"])
                normalized_size = normalize_size(product["size"])
                inferred_category = infer_category(product["name"], product["tags"])
                intent_key = f"{inferred_category.value}:{normalized_name}:{normalized_size.normalized_value or ''}{normalized_size.normalized_unit or ''}"

                canonical_row = conn.execute(
                    "SELECT id FROM canonical_products WHERE intent_key = ?",
                    (intent_key,),
                ).fetchone()
                if canonical_row:
                    canonical_id = canonical_row[0]
                else:
                    cur = conn.execute(
                        """
                        INSERT INTO canonical_products(
                            canonical_name, intent_key, category, normalized_brand,
                            normalized_unit, normalized_size_value, tags, searchable_text
                        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            normalized_name,
                            intent_key,
                            inferred_category.value,
                            normalized_brand,
                            normalized_size.normalized_unit or "",
                            normalized_size.normalized_value,
                            ",".join(normalized_tags),
                            build_searchable_text(product["name"], product["brand"], product["size"], product["tags"]),
                        ),
                    )
                    canonical_id = cur.lastrowid

                cur = conn.execute(
                    """
                    INSERT INTO raw_retailer_products(
                        retailer_id, source_name, source_brand, source_size, source_subcategory,
                        searchable_text, created_at
                    ) VALUES(?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        retailer_id,
                        product["name"],
                        product["brand"],
                        product["size"],
                        product["subcategory"],
                        build_searchable_text(product["name"], product["brand"], product["size"], product["tags"]),
                        datetime.now(UTC).isoformat(),
                    ),
                )
                raw_product_id = cur.lastrowid

                conn.execute(
                    "INSERT INTO product_mappings(raw_product_id, canonical_product_id, confidence, method) VALUES(?, ?, ?, ?)",
                    (raw_product_id, canonical_id, 1.0, "seed-normalized"),
                )
                conn.execute(
                    """
                    INSERT INTO price_snapshots(raw_product_id, price, currency, unit_description, unit_value, captured_at)
                    VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    (
                        raw_product_id,
                        float(Decimal(product["price"])),
                        "GBP",
                        product["unitDescription"],
                        float(Decimal(product["unitValue"])),
                        datetime.now(UTC).isoformat(),
                    ),
                )

        for synonym, canonical in {
            "beanz": "baked beans",
            "yoghurt": "yogurt",
            "loaf": "bread",
            "fillets": "fillet",
        }.items():
            conn.execute(
                "INSERT INTO search_synonyms(synonym, canonical_term, term_type) VALUES(?, ?, ?) ",
                (synonym, canonical, "catalog"),
            )
        conn.commit()


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
