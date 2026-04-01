# UKSupermarketCompare FastAPI Backend

This backend now serves the Swift app's live catalog payload with the exact JSON structure expected by `LiveSupermarketDataService`.

## Endpoints

- `GET /health`
- `GET /catalog`
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
- Swagger docs: `http://localhost:8000/docs`

## Swift setup

Set the Xcode Run environment variable:

- `LIVE_SUPERMARKET_DATA_URL=http://<your-machine-ip>:8000/catalog`

If running in the iOS Simulator on the same Mac, `http://localhost:8000/catalog` is fine.
