# UKSupermarketCompare FastAPI Backend

This backend now serves the Swift app's live catalog payload with the exact JSON structure expected by `LiveSupermarketDataService`.

## Platform milestone: scalable supermarket data backend

This milestone moves the backend from a seeded prototype toward a normalized, provider-driven platform:

- **Provider architecture layers are explicit**:
  - `providers/*` for retailer feed adapters
  - `ingestion.py` for import orchestration + canonical mapping + snapshot writes
  - `catalog_store.py` / `search_service.py` for serving read models
- **Canonical product scale support is improved**:
  - canonical rows now retain `canonical_aliases` and `token_fingerprint` for higher-quality matching across retailer naming variations
  - stronger normalization/tokenization helpers support large-catalog matching
- **Search/autocomplete hardening**:
  - ranking uses canonical aliases + token fingerprints + mapping confidence
  - quality telemetry captures misses and weak top matches
  - app-facing `/search` and `/autocomplete` response contracts remain unchanged
- **Price history + alert groundwork**:
  - snapshot indexing for larger history datasets
  - `price_drop_alert_candidates` table with automatic candidate creation when imports detect meaningful price drops
  - `basket_history` table added as foundational structure for future saved basket evolution
- **Observability improvements**:
  - diagnostics now include `priceSnapshots`, `priceDropAlertCandidates`, `weakMatches`, and `avgTopScore`
  - new milestone contract tests validate these backend/platform structures

## Endpoints

- `GET /health`
- `GET /catalog`
- `GET /search`
- `GET /autocomplete`
- `GET /diagnostics/catalog`
- `GET /diagnostics/search`
- `POST /compare` *(existing mock comparison route retained; app can ignore for now)*

## Comparison quality (Phase 1)

`POST /compare` now includes:

- richer free-text parsing (`2x milk`, `heinz baked beans`, `cheddar 400g`, preference words)
- synonym and typo-tolerant token expansion
- scored candidate matching using intent/category/tags/size clues
- explainability on matches (`reasons`, `tradeoffs`, `matchedTokens`, `score`)
- explainability on misses (`missingItemDetails` with close candidates + suggestions)

This is intentionally structured for future product phases (autocomplete ranking, user preferences, and provider-backed catalogs) without changing the Swift contract for existing fields.

## `/catalog` response shape

`/catalog` returns (plus live metadata marker):

```json
{
  "metadata": {
    "source": "live-backend",
    "debugMarker": "LIVE_CATALOG_V1",
    "generatedAt": "2026-04-01T00:00:00+00:00"
  },
  "supermarkets": [
    {
      "name": "Tesco",
      "description": "string",
      "products": [
        {
          "name": "string",
          "category": "milk",
          "subcategory": "string",
          "price": 1.55,
          "size": "string",
          "brand": "string",
          "isOwnBrand": true,
          "isPremium": false,
          "isOrganic": false,
          "unitDescription": "string",
          "unitValue": 0.775,
          "tags": ["string"]
        }
      ]
    }
  ]
}
```

Categories are constrained to the Swift `GroceryCategory` raw values:

`milk`, `bread`, `eggs`, `butter`, `pasta`, `bakedBeans`, `bananas`, `chickenBreast`, `cereal`, `cheese`, `tomatoes`, `rice`, `yogurt`, `apples`, `unknown`.


## Stage 3 Step 3: backend search + autocomplete

### `GET /search`

Backend-driven catalog search over normalized products and canonical mappings.

**Query parameters**

- `q` *(required, string)*: user search text
- `limit` *(optional, int, default `20`, max `50`)*: number of ranked product rows to return

**Behavior**

- exact + partial matching against normalized raw/canonical catalog text
- synonym expansion (via `search_synonyms`)
- fuzzy typo tolerance
- brand + size/unit token boosts
- ranking score that incorporates mapping confidence

**Response shape**

```json
{
  "query": "oatly milk",
  "normalizedQuery": "oatly milk",
  "total": 3,
  "results": [
    {
      "supermarket": "Tesco",
      "supermarketDescription": "...",
      "name": "Oatly Barista Oat Milk",
      "canonicalName": "oatly barista oat milk",
      "brand": "Oatly",
      "size": "1L",
      "category": "milk",
      "subcategory": "Dairy & Alternatives",
      "tags": ["oat", "barista"],
      "price": 2.0,
      "unitDescription": "per litre",
      "unitValue": 1.0,
      "score": 0.91,
      "matchType": "brand",
      "matchedTerms": ["milk", "oatly"]
    }
  ]
}
```

### `GET /autocomplete`

Fast add-item suggestions for iOS text entry. Uses search ranking then deduplicates by canonical item intent for short lists.

**Query parameters**

- `q` *(required, string)*: partial user input
- `limit` *(optional, int, default `8`, max `20`)*: number of suggestions

**Response shape**

```json
{
  "query": "semi skim",
  "total": 3,
  "suggestions": [
    {
      "suggestion": "tesco semi skimmed milk",
      "displayName": "Tesco Semi Skimmed Milk",
      "brand": "Tesco",
      "size": "2L",
      "category": "milk",
      "score": 0.87,
      "matchType": "partial"
    }
  ]
}
```

### iOS usage guidance

- Call `/autocomplete` on debounced keystrokes (e.g. 150–250ms).
- When the user submits search or taps “see all”, call `/search` for richer ranked rows.
- Continue using `/catalog` for full browsing and compatibility with existing Swift models.

## Stage 3 Step 2: provider architecture + import pipeline

### Providers

Retailer ingestion now uses provider abstractions in `app/services/providers/`:

- `TescoProvider`
- `AsdaProvider`
- `SainsburysProvider`

Each provider currently reads structured local import files from `app/data/imports/*.json`, then performs normalization and canonical intent-key generation through `app/services/normalization.py`. This keeps local development deterministic while remaining ready for future live feed adapters (the same provider contract can load from APIs, S3 feeds, etc).

### Ingestion workflow

Use the import command:

```bash
cd backend
python -m scripts.import_catalog
```

Optional reset-import per retailer:

```bash
python -m scripts.import_catalog --replace
```

Behavior:

- idempotent raw import matching (`retailer + source_product_id/name/brand/size`)
- canonical de-duplication via normalized `intent_key`
- mapping upsert for each raw product
- price snapshots only inserted when price/unit value changed

### Refresh local product data

1. Edit `app/data/imports/tesco.json`, `asda.json`, or `sainsburys.json`.
2. Re-run `python -m scripts.import_catalog`.
3. Restart API if needed and verify `GET /catalog`.

The seeded/import catalog now contains a substantially larger mixed product base (own-brand, branded, premium, and multiple size/variant combinations across all three supermarkets).

## Run locally (port 8000)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:

- API root: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Catalog: `http://localhost:8000/catalog`
- Diagnostics (catalog): `http://localhost:8000/diagnostics/catalog`
- Diagnostics (search): `http://localhost:8000/diagnostics/search`
- Swagger docs: `http://localhost:8000/docs`

## Diagnostics and catalog/search health

### Catalog diagnostics (`GET /diagnostics/catalog`)

Returns a compact health snapshot:

- `productsPerSupermarket`: raw product coverage by retailer
- `canonicalProducts`: canonical intent rows
- `mappings`: raw-to-canonical mapping rows
- `categoriesCovered`: distinct canonical categories currently represented
- `priceSnapshots`: current recorded snapshot count
- `priceDropAlertCandidates`: candidates identified for future price-drop notifications

Use this to quickly spot import issues (for example, a retailer showing `0` products or unexpectedly low mappings).

### Search diagnostics (`GET /diagnostics/search`)

Telemetry from `/search` + `/autocomplete` requests:

- `totalQueries`
- `missQueries` (queries with `0` results)
- `missRate`
- `weakMatches` (requests where top score was below quality threshold)
- `avgTopScore` across requests
- `byEndpoint` split (`/search` vs `/autocomplete`)

This gives a basic measurable signal of search health and potential intent-gaps.

## Troubleshooting

- If `/catalog` looks incomplete, run `python -m scripts.import_catalog --replace`, then re-check `/diagnostics/catalog`.
- If search quality regresses, inspect `/diagnostics/search` miss rate and review backend logs for `search_miss` / `autocomplete_miss`.
- If mappings drift, inspect logs for `Failed mappings detected` warnings.

## Validation checklist (Stage 3 Step 5)

1. Run tests: `pytest`.
2. Verify `/catalog` contract and category compatibility tests pass.
3. Verify `/search` and `/autocomplete` contract tests pass.
4. Hit `/diagnostics/catalog` and confirm expected non-zero counts.
5. Hit `/search` with known miss terms, then confirm `/diagnostics/search` miss metrics update.

## What remains before broader real-world data integration

1. Add live provider implementations (API, file drops, or crawling inputs) behind existing provider contracts.
2. Introduce async/batch ingestion workers and operational retry/idempotency controls for large feed updates.
3. Promote search telemetry to dashboarding/alerts (e.g., weak-match spikes by retailer/category).
4. Build first user-facing workflows for price-drop alerts and basket-history trend views backed by the new schema.

## Swift setup

Set the Xcode Run environment variable:

- `LIVE_SUPERMARKET_DATA_URL=http://<your-machine-ip>:8000/catalog`

If running in the iOS Simulator on the same Mac, `http://localhost:8000/catalog` is fine.


## Stage 4: live provider + enrichment

### Live provider configuration (Tesco)

The backend keeps the iOS app speaking only to FastAPI while allowing Tesco ingestion to switch source types behind the provider layer.

Environment variables:

- `TESCO_SOURCE_MODE` (`seed` by default)
  - `seed`: local deterministic import files
  - `structured` / `official` / `thirdparty` / `scrape`: enables the live Tesco adapter
- `TESCO_API_KEY`: required when non-seed mode is enabled
- `TESCO_SOURCE_BASE_URL`: structured Tesco-compatible API endpoint (default `https://api.trolley.co.uk/api/v1/products`)
- `TESCO_QUERY_TERMS`: comma-separated seed queries for pull/import (default `milk,bread,eggs,butter`)
- `OFF_BASE_URL`: Open Food Facts API base URL (default `https://world.openfoodfacts.org`)

### Running imports and cache refresh

```bash
cd backend
python -m scripts.import_catalog --replace
python -m scripts.import_catalog --tesco-live
```

Imports populate/update the local cache tables (`raw_retailer_products`, `product_mappings`, `canonical_products`, `price_snapshots`) so app requests do not require a remote fetch every time.

Cached fields now include retailer product id, price, promo price, size, unit pricing, brand, image, category tags, and last update timestamps.

### App-facing endpoints

- `GET /catalog` (legacy compatibility route retained)
- `GET /autocomplete`
- `GET /search`
- `GET /product/{id}` (optional enrichment via `?barcode=...`)
- `POST /compare`

### Open Food Facts enrichment

`GET /product/{id}?barcode=...` keeps enrichment separate from store pricing and returns product metadata, ingredients, nutrition, and allergens from Open Food Facts.

### What remains for ASDA / Sainsbury's

- Implement parallel live adapters equivalent to Tesco live source.
- Add scheduler/background jobs for periodic refresh and stale-data monitoring.
- Expand retailer-specific promo mechanics and unit normalization edge-cases.
