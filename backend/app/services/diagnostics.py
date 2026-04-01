from __future__ import annotations

from datetime import UTC, datetime

from app.db import get_connection


def record_search_event(*, query: str, normalized_query: str, result_count: int, endpoint: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO search_telemetry(query, normalized_query, result_count, endpoint, created_at)
            VALUES(?, ?, ?, ?, ?)
            """,
            (query, normalized_query, result_count, endpoint, datetime.now(UTC).isoformat()),
        )
        conn.commit()


def record_search_quality_event(
    *,
    query: str,
    normalized_query: str,
    endpoint: str,
    top_score: float,
    weak_match: bool,
    miss: bool,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO search_quality_events(
                query, normalized_query, endpoint, top_score, weak_match, miss, created_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (query, normalized_query, endpoint, top_score, int(weak_match), int(miss), datetime.now(UTC).isoformat()),
        )
        conn.commit()


def catalog_diagnostics() -> dict:
    with get_connection() as conn:
        per_market_rows = conn.execute(
            """
            SELECT r.name AS supermarket, COUNT(raw.id) AS products
            FROM retailers r
            LEFT JOIN raw_retailer_products raw ON raw.retailer_id = r.id
            GROUP BY r.id, r.name
            ORDER BY r.name
            """
        ).fetchall()
        canonical_count = conn.execute("SELECT COUNT(*) AS count FROM canonical_products").fetchone()["count"]
        mapping_count = conn.execute("SELECT COUNT(*) AS count FROM product_mappings").fetchone()["count"]
        categories = conn.execute(
            "SELECT DISTINCT category FROM canonical_products WHERE TRIM(category) <> '' ORDER BY category"
        ).fetchall()
        snapshot_rows = conn.execute("SELECT COUNT(*) AS count FROM price_snapshots").fetchone()["count"]
        alert_candidates = conn.execute("SELECT COUNT(*) AS count FROM price_drop_alert_candidates").fetchone()["count"]

    return {
        "productsPerSupermarket": [{"supermarket": row["supermarket"], "products": row["products"]} for row in per_market_rows],
        "canonicalProducts": canonical_count,
        "mappings": mapping_count,
        "categoriesCovered": [row["category"] for row in categories],
        "priceSnapshots": int(snapshot_rows or 0),
        "priceDropAlertCandidates": int(alert_candidates or 0),
    }


def search_diagnostics() -> dict:
    with get_connection() as conn:
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS total_queries,
                SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END) AS miss_queries
            FROM search_telemetry
            """
        ).fetchone()
        per_endpoint = conn.execute(
            """
            SELECT endpoint, COUNT(*) AS total, SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END) AS misses
            FROM search_telemetry
            GROUP BY endpoint
            ORDER BY endpoint
            """
        ).fetchall()
        quality = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN weak_match = 1 THEN 1 ELSE 0 END) AS weak_matches,
                AVG(top_score) AS avg_top_score
            FROM search_quality_events
            """
        ).fetchone()

    total_queries = int(totals["total_queries"] or 0)
    miss_queries = int(totals["miss_queries"] or 0)
    miss_rate = round((miss_queries / total_queries), 4) if total_queries else 0.0

    return {
        "totalQueries": total_queries,
        "missQueries": miss_queries,
        "missRate": miss_rate,
        "weakMatches": int(quality["weak_matches"] or 0),
        "avgTopScore": round(float(quality["avg_top_score"] or 0.0), 4),
        "byEndpoint": [
            {
                "endpoint": row["endpoint"],
                "totalQueries": int(row["total"] or 0),
                "missQueries": int(row["misses"] or 0),
            }
            for row in per_endpoint
        ],
    }


def tesco_live_diagnostics() -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT raw.source_metadata, raw.last_updated
            FROM raw_retailer_products raw
            JOIN retailers r ON r.id = raw.retailer_id
            WHERE r.name = 'Tesco'
            ORDER BY raw.last_updated DESC
            LIMIT 1
            """
        ).fetchone()

    if not row:
        return {"mode": "fallback", "activeSource": "none", "status": "empty", "lastUpdated": None}

    source_metadata = (row["source_metadata"] or "").lower()
    active_source = "seed"
    if "official" in source_metadata:
        active_source = "official"
    elif "third_party" in source_metadata:
        active_source = "third_party"

    if active_source == "seed":
        status = "fallback"
    else:
        status = "active"
    return {"mode": active_source, "activeSource": active_source, "status": status, "lastUpdated": row["last_updated"] or None}
