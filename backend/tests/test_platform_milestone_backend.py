from app.db import init_db, get_connection
from app.services.catalog_store import ensure_seed_data
from app.services.ingestion import import_catalog_data
from app.routes.search import search
from app.routes.diagnostics import catalog_metrics, search_metrics


def setup_module() -> None:
    init_db()
    ensure_seed_data()


def test_canonical_products_have_aliases_and_fingerprint() -> None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT canonical_aliases, token_fingerprint
            FROM canonical_products
            WHERE TRIM(canonical_aliases) <> ''
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row["canonical_aliases"]
    assert row["token_fingerprint"]


def test_search_quality_metrics_track_weak_and_miss_queries() -> None:
    search(q="milk", limit=5)
    search(q="qwertyuiop-no-match", limit=5)

    payload = search_metrics().model_dump(mode="json")

    assert payload["totalQueries"] >= 2
    assert payload["missQueries"] >= 1
    assert "weakMatches" in payload
    assert "avgTopScore" in payload


def test_price_history_and_alert_structures_exist_after_import() -> None:
    import_catalog_data(replace_existing=False)

    payload = catalog_metrics().model_dump(mode="json")

    assert payload["priceSnapshots"] > 0
    assert "priceDropAlertCandidates" in payload
