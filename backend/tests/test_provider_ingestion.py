from pathlib import Path

from app import db
from app.services.ingestion import import_catalog_data
from app.services.providers import AsdaProvider, SainsburysProvider, TescoProvider


def _count(conn, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_provider_loading_and_normalization_contract():
    provider = TescoProvider()
    rows = provider.load_products()
    normalized = provider.normalize_products()

    assert rows
    assert len(rows) == len(normalized)
    assert all(row.intent_key for row in normalized)
    assert all(row.searchable_text for row in normalized)


def test_import_is_repeatable_and_avoids_duplicate_raw_products(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "catalog.db")

    db.init_db()
    first = import_catalog_data()
    second = import_catalog_data()

    with db.get_connection() as conn:
        raw_count = _count(conn, "raw_retailer_products")
        map_count = _count(conn, "product_mappings")
        price_count = _count(conn, "price_snapshots")
        run_count = _count(conn, "import_runs")
        successful_runs = conn.execute("SELECT COUNT(*) AS count FROM import_runs WHERE status = 'success'").fetchone()["count"]

    assert first["inserted_raw"] > 0
    assert second["inserted_raw"] == 0
    assert raw_count == map_count
    assert price_count == raw_count
    assert run_count == 6
    assert successful_runs == run_count


def test_import_creates_cross_provider_canonical_mappings(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "catalog.db")

    db.init_db()
    import_catalog_data(providers=[TescoProvider(), AsdaProvider(), SainsburysProvider()])

    with db.get_connection() as conn:
        raw_count = _count(conn, "raw_retailer_products")
        canonical_count = _count(conn, "canonical_products")
        heinz_rows = conn.execute(
            """
            SELECT COUNT(DISTINCT r.name) AS markets
            FROM raw_retailer_products raw
            JOIN retailers r ON r.id = raw.retailer_id
            JOIN product_mappings pm ON pm.raw_product_id = raw.id
            JOIN canonical_products cp ON cp.id = pm.canonical_product_id
            WHERE raw.source_brand = 'Heinz' AND cp.intent_key LIKE 'bakedBeans:%'
            """
        ).fetchone()["markets"]

    assert raw_count > 100
    assert canonical_count < raw_count
    assert heinz_rows >= 2
