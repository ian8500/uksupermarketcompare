# Live data roadmap (recommended next implementation)

This project already has the right foundations for live data:

- provider abstractions (`app/services/providers/*`)
- normalized ingestion (`app/services/ingestion.py`)
- stable app-facing routes (`/catalog`, `/search`, `/autocomplete`, `/product/{id}`, `/compare`)
- diagnostics endpoints

The best next step is to move from "Tesco-only live when configured" to **operator-visible, freshness-governed live ingestion for all providers**.

## 1) Add scheduled imports with freshness SLOs (highest impact)

Implement a background import schedule and explicit freshness targets.

### Why
- Today imports are primarily manual (`python -m scripts.import_catalog`).
- Live data quality depends on predictable refreshes and stale-data detection.

### What to add
- A periodic job (e.g., every 30–120 minutes) that runs `import_catalog_data()`.
- Per-retailer freshness objective (example: "critical if last successful import > 6h").
- Import outcome metrics:
  - success/failure
  - duration
  - rows fetched/mapped
  - source mode used (`seed`, `official`, `third_party`)

### Done looks like
- `GET /diagnostics/catalog` includes per-retailer last-success timestamp + freshness status.
- Stale state is machine-readable (for alerts and app debug surfaces).

## 2) Add live adapters for ASDA and Sainsbury's behind existing provider interfaces

Keep all provider-specific parsing in adapters and continue writing normalized products.

### Why
- `AsdaProvider` and `SainsburysProvider` currently use seed files only.
- Multi-retailer live coverage unlocks meaningful compare outcomes.

### What to add
- `AsdaLiveSource` and `SainsburysLiveSource` classes with the same resilience pattern as Tesco:
  - explicit `is_configured()` checks
  - bounded retries/timeouts
  - partial-failure reporting
  - dedupe before normalize/import
- Environment-based mode selection (`auto`, `official`, `third_party`, `seed`) per retailer.

### Done looks like
- Import runs report live source mode by retailer in `import_runs`.
- Contract endpoints are unchanged; only backing data improves.

## 3) Add ingestion guardrails for mapping drift

You already track mapped/unmapped counts. Add explicit thresholds and actions.

### Why
- Live feeds drift (names, sizes, units, brands).
- Silent drift degrades search and compare quality.

### What to add
- Threshold checks during import (warn/critical when mapping ratio drops).
- Store top unmapped examples for fast operator diagnosis.
- Extend diagnostics with rolling mapping quality by retailer.

### Done looks like
- Drift is visible within one import cycle.
- Operators can identify whether drift is provider-side or normalization-side.

## 4) Add provenance in read models (non-breaking)

Expose where each product row came from without changing route contracts.

### Why
- Useful for debugging trust/freshness questions in app and backend.

### What to add
- Internal read-model fields for:
  - `retailer_source_mode`
  - `captured_at`
  - `import_run_id`
- Keep app-facing response schema unchanged unless intentionally extended in a backward-compatible way.

## 5) Productionize import execution path

### Why
- Local/manual commands don't provide operational reliability alone.

### What to add
- A deployable worker/cron entrypoint that runs imports.
- Structured logs with redaction (no API keys in logs).
- Runbook for key failures:
  - auth failure
  - upstream timeout
  - zero-row imports
  - mapping drop

## Suggested implementation order

1. Freshness + scheduled imports
2. ASDA live adapter
3. Sainsbury's live adapter
4. Mapping drift diagnostics
5. Provenance fields + runbook polish

## Minimal first increment (1-2 days)

- Add scheduler hook for `import_catalog_data()`.
- Add per-retailer freshness fields to `/diagnostics/catalog`.
- Add one alert condition: stale if no successful import for Tesco within 6h.

This gives immediate operational confidence while keeping all public contracts stable.
