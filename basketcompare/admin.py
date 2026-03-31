from __future__ import annotations

from .comparison import BasketComparisonService


def build_debug_screen(service: BasketComparisonService) -> list[dict]:
    rows = []
    for row in service.debug_rows():
        rows.append(
            {
                "provider": row.raw_product.provider,
                "sku": row.raw_product.sku,
                "raw_title": row.raw_product.title,
                "canonical_name": row.canonical.canonical_name,
                "brand": row.canonical.normalized_brand,
                "category": row.canonical.category,
                "pack": row.metadata["normalized_pack"],
                "tokens": list(row.metadata["tokens"]),
            }
        )
    return rows
