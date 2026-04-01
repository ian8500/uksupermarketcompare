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
        latest_runs = conn.execute(
            """
            SELECT
                ir.retailer,
                ir.source_mode,
                ir.started_at,
                ir.completed_at,
                ir.duration_ms,
                ir.status,
                ir.fetched_count,
                ir.inserted_count,
                ir.updated_count,
                ir.mapped_count,
                ir.unmapped_count,
                ir.snapshot_count,
                ir.error_count,
                ir.error_details
            FROM import_runs ir
            JOIN (
                SELECT retailer, MAX(started_at) AS max_started_at
                FROM import_runs
                GROUP BY retailer
            ) latest ON latest.retailer = ir.retailer AND latest.max_started_at = ir.started_at
            ORDER BY ir.retailer
            """
        ).fetchall()

    return {
        "productsPerSupermarket": [{"supermarket": row["supermarket"], "products": row["products"]} for row in per_market_rows],
        "canonicalProducts": canonical_count,
        "mappings": mapping_count,
        "categoriesCovered": [row["category"] for row in categories],
        "priceSnapshots": int(snapshot_rows or 0),
        "priceDropAlertCandidates": int(alert_candidates or 0),
        "retailerFreshness": retailer_freshness_diagnostics(),
        "latestImportRuns": [
            {
                "retailer": row["retailer"],
                "sourceMode": row["source_mode"],
                "startedAt": row["started_at"],
                "completedAt": row["completed_at"],
                "durationMs": row["duration_ms"],
                "status": row["status"],
                "fetchedCount": int(row["fetched_count"] or 0),
                "insertedCount": int(row["inserted_count"] or 0),
                "updatedCount": int(row["updated_count"] or 0),
                "mappedCount": int(row["mapped_count"] or 0),
                "unmappedCount": int(row["unmapped_count"] or 0),
                "snapshotCount": int(row["snapshot_count"] or 0),
                "errorCount": int(row["error_count"] or 0),
                "errorDetails": row["error_details"] or "[]",
            }
            for row in latest_runs
        ],
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


def retailer_freshness_diagnostics() -> list[dict[str, str | int | None]]:
    now = datetime.now(UTC)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                r.name AS retailer,
                (
                    SELECT ir.started_at
                    FROM import_runs ir
                    WHERE ir.retailer = r.name
                    ORDER BY ir.started_at DESC
                    LIMIT 1
                ) AS last_attempt_at,
                (
                    SELECT ir.status
                    FROM import_runs ir
                    WHERE ir.retailer = r.name
                    ORDER BY ir.started_at DESC
                    LIMIT 1
                ) AS last_status,
                (
                    SELECT ir.completed_at
                    FROM import_runs ir
                    WHERE ir.retailer = r.name AND ir.status = 'success'
                    ORDER BY ir.completed_at DESC
                    LIMIT 1
                ) AS last_success_at
            FROM retailers r
            ORDER BY r.name
            """
        ).fetchall()

    payload: list[dict[str, str | int | None]] = []
    for row in rows:
        last_success_at = row["last_success_at"]
        last_status = row["last_status"] or "unknown"
        age_hours: int | None = None
        if last_success_at:
            success_dt = datetime.fromisoformat(last_success_at.replace("Z", "+00:00"))
            age_hours = int((now - success_dt).total_seconds() // 3600)

        if last_status == "failed" and (age_hours is None or age_hours > 24):
            freshness = "failed"
        elif age_hours is None:
            freshness = "critical"
        elif age_hours <= 24:
            freshness = "healthy"
        elif age_hours <= 72:
            freshness = "stale"
        else:
            freshness = "critical"

        payload.append(
            {
                "retailer": row["retailer"],
                "status": freshness,
                "ageHours": age_hours,
                "lastAttemptAt": row["last_attempt_at"],
                "lastSuccessAt": last_success_at,
                "lastImportStatus": last_status,
            }
        )
    return payload
