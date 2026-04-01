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
                searchable_text TEXT NOT NULL
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
            """
        )
