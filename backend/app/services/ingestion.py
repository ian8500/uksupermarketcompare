from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from dataclasses import dataclass

from app.db import get_connection
from app.services.providers import AsdaProvider, SainsburysProvider, SupermarketPriceProvider, TescoProvider

DEFAULT_SYNONYMS: dict[str, str] = {
    "beanz": "baked beans",
    "yoghurt": "yogurt",
    "loaf": "bread",
    "fillets": "fillet",
}
logger = logging.getLogger(__name__)


@dataclass
class ImportRunState:
    run_id: int
    retailer: str
    source_mode: str
    started_at: datetime
    fetched_count: int = 0
    inserted_count: int = 0
    updated_count: int = 0
    mapped_count: int = 0
    snapshot_count: int = 0
    error_count: int = 0
    errors: list[str] | None = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []

    @property
    def unmapped_count(self) -> int:
        return max(0, self.fetched_count - self.mapped_count)

    def record_error(self, exc: Exception) -> None:
        self.error_count += 1
        self.errors.append(str(exc))


def _insert_import_run(conn, *, retailer: str, source_mode: str) -> ImportRunState:
    started_at = datetime.now(UTC)
    run_id = conn.execute(
        """
        INSERT INTO import_runs(retailer, source_mode, started_at, status)
        VALUES(?, ?, ?, ?)
        """,
        (retailer, source_mode, started_at.isoformat(), "running"),
    ).lastrowid
    return ImportRunState(run_id=run_id, retailer=retailer, source_mode=source_mode, started_at=started_at)


def _persist_import_run(conn, state: ImportRunState, *, status: str, completed_at: datetime | None = None) -> None:
    completed = completed_at or datetime.now(UTC)
    duration_ms = int((completed - state.started_at).total_seconds() * 1000)
    conn.execute(
        """
        UPDATE import_runs
        SET source_mode = ?, completed_at = ?, duration_ms = ?, status = ?, fetched_count = ?, inserted_count = ?,
            updated_count = ?, mapped_count = ?, unmapped_count = ?, snapshot_count = ?, error_count = ?, error_details = ?
        WHERE id = ?
        """,
        (
            state.source_mode,
            completed.isoformat(),
            duration_ms,
            status,
            state.fetched_count,
            state.inserted_count,
            state.updated_count,
            state.mapped_count,
            state.unmapped_count,
            state.snapshot_count,
            state.error_count,
            json.dumps(state.errors),
            state.run_id,
        ),
    )


def default_providers() -> list[SupermarketPriceProvider]:
    return [TescoProvider(), AsdaProvider(), SainsburysProvider()]


def import_catalog_data(providers: list[SupermarketPriceProvider] | None = None, *, replace_existing: bool = False) -> dict[str, int]:
    providers = providers or default_providers()
    inserted_raw = 0
    updated_raw = 0
    inserted_canonical = 0
    inserted_price_snapshots = 0
    inserted_price_drop_candidates = 0

    with get_connection() as conn:
        for provider in providers:
            source_mode = getattr(provider, "active_source", "seed")
            run_state = _insert_import_run(conn, retailer=provider.name, source_mode=source_mode)
            logger.info("Starting import for provider=%s replace_existing=%s", provider.name, replace_existing)
            retailer_row = conn.execute("SELECT id FROM retailers WHERE name = ?", (provider.name,)).fetchone()
            if retailer_row:
                retailer_id = retailer_row[0]
                conn.execute("UPDATE retailers SET description = ? WHERE id = ?", (provider.description, retailer_id))
            else:
                retailer_id = conn.execute(
                    "INSERT INTO retailers(name, description) VALUES(?, ?)", (provider.name, provider.description)
                ).lastrowid

            if replace_existing:
                conn.execute(
                    "DELETE FROM price_snapshots WHERE raw_product_id IN (SELECT id FROM raw_retailer_products WHERE retailer_id = ?)",
                    (retailer_id,),
                )
                conn.execute(
                    "DELETE FROM product_mappings WHERE raw_product_id IN (SELECT id FROM raw_retailer_products WHERE retailer_id = ?)",
                    (retailer_id,),
                )
                conn.execute("DELETE FROM raw_retailer_products WHERE retailer_id = ?", (retailer_id,))

            try:
                normalized_products = provider.normalize_products()
                provider_report = getattr(provider, "last_import_report", {}) or {}
                run_state.fetched_count = int(provider_report.get("fetched", len(normalized_products)))
                run_state.source_mode = getattr(provider, "active_source", source_mode)

                for product in normalized_products:
                    canonical_row = conn.execute(
                        "SELECT id FROM canonical_products WHERE intent_key = ?", (product.intent_key,)
                    ).fetchone()
                    if canonical_row:
                        canonical_id = canonical_row[0]
                        conn.execute(
                            """
                            UPDATE canonical_products
                            SET searchable_text = ?, tags = ?, canonical_aliases = ?, token_fingerprint = ?
                            WHERE id = ?
                            """,
                            (
                                product.searchable_text,
                                ",".join(product.normalized_tags),
                                ",".join(product.canonical_aliases),
                                product.token_fingerprint,
                                canonical_id,
                            ),
                        )
                    else:
                        canonical_id = conn.execute(
                            """
                            INSERT INTO canonical_products(
                                canonical_name, intent_key, category, normalized_brand,
                                normalized_unit, normalized_size_value, tags, searchable_text, token_fingerprint, canonical_aliases
                            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                product.normalized_name,
                                product.intent_key,
                                product.category.value,
                                product.normalized_brand,
                                product.normalized_size.normalized_unit or "",
                                product.normalized_size.normalized_value,
                                ",".join(product.normalized_tags),
                                product.searchable_text,
                                product.token_fingerprint,
                                ",".join(product.canonical_aliases),
                            ),
                        ).lastrowid
                        inserted_canonical += 1

                    raw_row = conn.execute(
                        """
                        SELECT id FROM raw_retailer_products
                        WHERE retailer_id = ?
                        AND COALESCE(source_product_id, '') = COALESCE(?, '')
                        AND source_name = ? AND source_brand = ? AND source_size = ?
                        """,
                        (
                            retailer_id,
                            product.raw.source_product_id,
                            product.raw.name,
                            product.raw.brand,
                            product.raw.size,
                        ),
                    ).fetchone()

                    now = datetime.now(UTC).isoformat()
                    if raw_row:
                        raw_product_id = raw_row[0]
                        conn.execute(
                            """
                            UPDATE raw_retailer_products
                            SET source_subcategory = ?, searchable_text = ?, image_url = ?, category_tags = ?, availability = ?, source_metadata = ?, last_updated = ?, created_at = ?
                            WHERE id = ?
                            """,
                            (
                                product.raw.subcategory,
                                product.searchable_text,
                                product.raw.image_url or "",
                                ",".join(product.normalized_tags),
                                product.raw.availability or "",
                                json.dumps(product.raw.source_metadata or {}, sort_keys=True),
                                product.raw.last_updated or now,
                                now,
                                raw_product_id,
                            ),
                        )
                        updated_raw += 1
                        run_state.updated_count += 1
                    else:
                        raw_product_id = conn.execute(
                            """
                            INSERT INTO raw_retailer_products(
                                retailer_id, source_product_id, source_name, source_brand, source_size, source_subcategory,
                                image_url, category_tags, availability, source_metadata, last_updated, searchable_text, created_at
                            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                retailer_id,
                                product.raw.source_product_id,
                                product.raw.name,
                                product.raw.brand,
                                product.raw.size,
                                product.raw.subcategory,
                                product.raw.image_url or "",
                                ",".join(product.normalized_tags),
                                product.raw.availability or "",
                                json.dumps(product.raw.source_metadata or {}, sort_keys=True),
                                product.raw.last_updated or now,
                                product.searchable_text,
                                now,
                            ),
                        ).lastrowid
                        inserted_raw += 1
                        run_state.inserted_count += 1

                    conn.execute(
                        """
                        INSERT INTO product_mappings(raw_product_id, canonical_product_id, confidence, method)
                        VALUES(?, ?, ?, ?)
                        ON CONFLICT(raw_product_id) DO UPDATE SET
                            canonical_product_id = excluded.canonical_product_id,
                            confidence = excluded.confidence,
                            method = excluded.method
                        """,
                        (raw_product_id, canonical_id, 1.0, f"{provider.name.lower()}-normalized"),
                    )
                    run_state.mapped_count += 1

                    latest = conn.execute(
                        """
                        SELECT price, unit_value, promo_price FROM price_snapshots
                        WHERE raw_product_id = ?
                        ORDER BY captured_at DESC LIMIT 1
                        """,
                        (raw_product_id,),
                    ).fetchone()
                    new_price = float(product.raw.price)
                    new_unit_value = float(product.raw.unit_value)
                    new_promo_price = float(product.raw.promo_price) if product.raw.promo_price is not None else None
                    if (
                        not latest
                        or latest["price"] != new_price
                        or latest["unit_value"] != new_unit_value
                        or latest["promo_price"] != new_promo_price
                    ):
                        if latest and latest["price"] > 0 and new_price < latest["price"]:
                            change_ratio = round((latest["price"] - new_price) / latest["price"], 4)
                            if change_ratio >= 0.05:
                                conn.execute(
                                    """
                                    INSERT INTO price_drop_alert_candidates(
                                        raw_product_id, previous_price, latest_price, change_ratio, status, detected_at
                                    ) VALUES(?, ?, ?, ?, ?, ?)
                                    """,
                                    (raw_product_id, latest["price"], new_price, change_ratio, "candidate", now),
                                )
                                inserted_price_drop_candidates += 1
                        conn.execute(
                            """
                            INSERT INTO price_snapshots(raw_product_id, price, currency, unit_description, unit_value, promo_price, captured_at)
                            VALUES(?, ?, ?, ?, ?, ?, ?)
                            """,
                            (raw_product_id, new_price, "GBP", product.raw.unit_description, new_unit_value, new_promo_price, now),
                        )
                        inserted_price_snapshots += 1
                        run_state.snapshot_count += 1
            except Exception as exc:
                run_state.record_error(exc)
                _persist_import_run(conn, run_state, status="failed")
                logger.exception("Import failed for provider=%s", provider.name)
                continue

            _persist_import_run(conn, run_state, status="success")
            logger.info(
                "Completed import provider=%s source=%s fetched=%d skipped=%d rejected=%d inserted=%d updated=%d mapped=%d unmapped=%d snapshots=%d",
                provider.name,
                run_state.source_mode,
                run_state.fetched_count,
                int(provider_report.get("skipped", 0)),
                int(provider_report.get("rejected", 0)),
                run_state.inserted_count,
                run_state.updated_count,
                run_state.mapped_count,
                run_state.unmapped_count,
                run_state.snapshot_count,
            )

        for synonym, canonical in DEFAULT_SYNONYMS.items():
            conn.execute(
                "INSERT OR IGNORE INTO search_synonyms(synonym, canonical_term, term_type) VALUES(?, ?, ?)",
                (synonym, canonical, "catalog"),
            )
        conn.commit()
    logger.info(
        "Import finished providers=%d inserted_raw=%d updated_raw=%d inserted_canonical=%d inserted_price_snapshots=%d inserted_price_drop_candidates=%d",
        len(providers),
        inserted_raw,
        updated_raw,
        inserted_canonical,
        inserted_price_snapshots,
        inserted_price_drop_candidates,
    )

    return {
        "providers": len(providers),
        "inserted_raw": inserted_raw,
        "updated_raw": updated_raw,
        "inserted_canonical": inserted_canonical,
        "inserted_price_snapshots": inserted_price_snapshots,
        "inserted_price_drop_candidates": inserted_price_drop_candidates,
    }
