from __future__ import annotations

import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parents[1] / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "uksupermarketcompare.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS retailers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS raw_retailer_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                retailer_id INTEGER NOT NULL,
                source_product_id TEXT,
                source_name TEXT NOT NULL,
                source_brand TEXT NOT NULL,
                source_size TEXT NOT NULL,
                source_subcategory TEXT NOT NULL,
                raw_payload TEXT,
                image_url TEXT NOT NULL DEFAULT "",
                category_tags TEXT NOT NULL DEFAULT "",
                availability TEXT NOT NULL DEFAULT "",
                source_metadata TEXT NOT NULL DEFAULT "{}",
                last_updated TEXT NOT NULL DEFAULT "",
                searchable_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(retailer_id) REFERENCES retailers(id)
            );

            CREATE TABLE IF NOT EXISTS canonical_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_name TEXT NOT NULL,
                intent_key TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                normalized_brand TEXT NOT NULL,
                normalized_unit TEXT NOT NULL,
                normalized_size_value REAL,
                tags TEXT NOT NULL,
                searchable_text TEXT NOT NULL,
                token_fingerprint TEXT NOT NULL DEFAULT '',
                canonical_aliases TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS product_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_product_id INTEGER NOT NULL UNIQUE,
                canonical_product_id INTEGER NOT NULL,
                confidence REAL NOT NULL,
                method TEXT NOT NULL,
                FOREIGN KEY(raw_product_id) REFERENCES raw_retailer_products(id),
                FOREIGN KEY(canonical_product_id) REFERENCES canonical_products(id)
            );

            CREATE TABLE IF NOT EXISTS price_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                currency TEXT NOT NULL,
                unit_description TEXT NOT NULL,
                unit_value REAL NOT NULL,
                promo_price REAL,
                captured_at TEXT NOT NULL,
                FOREIGN KEY(raw_product_id) REFERENCES raw_retailer_products(id)
            );

            CREATE TABLE IF NOT EXISTS search_synonyms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                synonym TEXT NOT NULL UNIQUE,
                canonical_term TEXT NOT NULL,
                term_type TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS search_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                normalized_query TEXT NOT NULL,
                result_count INTEGER NOT NULL,
                endpoint TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS search_quality_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                normalized_query TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                top_score REAL NOT NULL,
                weak_match INTEGER NOT NULL,
                miss INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS basket_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                basket_key TEXT NOT NULL,
                supermarket_count INTEGER NOT NULL,
                total REAL NOT NULL,
                unavailable_items INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS price_drop_alert_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_product_id INTEGER NOT NULL,
                previous_price REAL NOT NULL,
                latest_price REAL NOT NULL,
                change_ratio REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'candidate',
                detected_at TEXT NOT NULL,
                FOREIGN KEY(raw_product_id) REFERENCES raw_retailer_products(id)
            );

            CREATE TABLE IF NOT EXISTS import_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                retailer TEXT NOT NULL,
                source_mode TEXT NOT NULL DEFAULT 'seed',
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                fetched_count INTEGER NOT NULL DEFAULT 0,
                inserted_count INTEGER NOT NULL DEFAULT 0,
                updated_count INTEGER NOT NULL DEFAULT 0,
                mapped_count INTEGER NOT NULL DEFAULT 0,
                unmapped_count INTEGER NOT NULL DEFAULT 0,
                snapshot_count INTEGER NOT NULL DEFAULT 0,
                error_count INTEGER NOT NULL DEFAULT 0,
                error_details TEXT NOT NULL DEFAULT '[]'
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_price_snapshots_raw_time ON price_snapshots(raw_product_id, captured_at DESC)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_canonical_intent_category ON canonical_products(intent_key, category)"
        )
        _ensure_column(conn, "canonical_products", "token_fingerprint", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "canonical_products", "canonical_aliases", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "raw_retailer_products", "image_url", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "raw_retailer_products", "category_tags", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "raw_retailer_products", "availability", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "raw_retailer_products", "source_metadata", "TEXT NOT NULL DEFAULT '{}'")
        _ensure_column(conn, "raw_retailer_products", "last_updated", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "price_snapshots", "promo_price", "REAL")
        _ensure_column(conn, "import_runs", "source_mode", "TEXT NOT NULL DEFAULT 'seed'")
        _ensure_column(conn, "import_runs", "fetched_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "import_runs", "inserted_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "import_runs", "updated_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "import_runs", "mapped_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "import_runs", "unmapped_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "import_runs", "snapshot_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "import_runs", "error_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "import_runs", "error_details", "TEXT NOT NULL DEFAULT '[]'")
        conn.commit()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if any(row["name"] == column for row in cols):
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
