from pathlib import Path
from decimal import Decimal

from app import db
from app.models import GroceryCategory
from app.services.normalization import NormalizedSize
from app.services.ingestion import import_catalog_data
from app.services.providers import AsdaProvider, SainsburysProvider, TescoProvider
from app.services.providers.base import NormalizedProviderProduct, ProviderProduct


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


def test_successful_import_run_is_created(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "catalog.db")

    db.init_db()
    import_catalog_data(providers=[TescoProvider()])

    with db.get_connection() as conn:
        run = conn.execute(
            "SELECT retailer, source_mode, started_at, completed_at, duration_ms, status FROM import_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert run is not None
    assert run["retailer"] == "Tesco"
    assert run["source_mode"] in {"seed", "official", "third_party"}
    assert run["started_at"] is not None
    assert run["completed_at"] is not None
    assert run["duration_ms"] is not None
    assert run["status"] == "success"


class FailingProvider:
    name = "FailMart"
    description = "Provider that fails during normalization"
    active_source = "seed"

    def load_products(self) -> list[ProviderProduct]:
        return []

    def normalize_products(self) -> list[NormalizedProviderProduct]:
        raise RuntimeError("provider exploded")


class BrokenSetupProvider:
    name = "BrokenSetupMart"
    active_source = "seed"

    @property
    def description(self) -> str:
        raise RuntimeError("description missing")

    def load_products(self) -> list[ProviderProduct]:
        return []

    def normalize_products(self) -> list[NormalizedProviderProduct]:
        return []


def test_failed_import_run_is_recorded(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "catalog.db")

    db.init_db()
    import_catalog_data(providers=[FailingProvider()])

    with db.get_connection() as conn:
        run = conn.execute(
            "SELECT status, error_count, error_details, fetched_count, mapped_count FROM import_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert run is not None
    assert run["status"] == "failed"
    assert run["error_count"] == 1
    assert "provider exploded" in run["error_details"]
    assert run["fetched_count"] == 0
    assert run["mapped_count"] == 0


def test_failed_import_run_is_recorded_for_setup_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "catalog.db")

    db.init_db()
    import_catalog_data(providers=[BrokenSetupProvider()])

    with db.get_connection() as conn:
        run = conn.execute(
            "SELECT status, error_count, error_details FROM import_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert run is not None
    assert run["status"] == "failed"
    assert run["error_count"] == 1
    assert "description missing" in run["error_details"]


class SingleProductProvider:
    name = "SingleMart"
    description = "Single product provider"
    active_source = "seed"

    def load_products(self) -> list[ProviderProduct]:
        return []

    def normalize_products(self) -> list[NormalizedProviderProduct]:
        product = ProviderProduct(
            source_product_id="sku-1",
            name="Single Milk",
            subcategory="milk",
            price=Decimal("1.25"),
            size="1L",
            brand="Single",
            unit_description="per litre",
            unit_value=Decimal("1"),
            tags=["milk"],
            source_metadata={"source": "seed"},
        )
        return [
            NormalizedProviderProduct(
                raw=product,
                retailer_name=self.name,
                normalized_name="single milk",
                normalized_brand="single",
                normalized_tags=["milk"],
                normalized_size=NormalizedSize(original="1L", value=1.0, unit="l", normalized_value=1000.0, normalized_unit="ml"),
                category=GroceryCategory.milk,
                searchable_text="single milk single milk 1000ml",
                intent_key="milk:single milk:1000.0ml",
                canonical_aliases=["single", "single milk"],
                token_fingerprint="milk|single",
            )
        ]


def test_import_run_counts_are_populated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "catalog.db")

    db.init_db()
    import_catalog_data(providers=[SingleProductProvider()])

    with db.get_connection() as conn:
        run = conn.execute(
            """
            SELECT fetched_count, inserted_count, updated_count, mapped_count, unmapped_count, snapshot_count, error_count
            FROM import_runs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert run is not None
    assert run["fetched_count"] == 1
    assert run["inserted_count"] == 1
    assert run["updated_count"] == 0
    assert run["mapped_count"] == 1
    assert run["unmapped_count"] == 0
    assert run["snapshot_count"] == 1
    assert run["error_count"] == 0
