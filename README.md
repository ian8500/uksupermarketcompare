# UK Supermarket Compare (iOS SwiftUI)

This repository contains a native iPhone app built with Swift and SwiftUI, plus a FastAPI backend that can serve a live supermarket catalog.

## Open in Xcode

1. Open `UKSupermarketCompare.xcodeproj` in Xcode 16+.
2. Select an iPhone simulator (e.g., iPhone 16).
3. Build and run.

## Current app capabilities (Stages 1–4)

- Welcome / Home, list creation, supermarket selection, results, and saved baskets.
- Local persistence of saved lists via `UserDefaults`.
- Live backend catalog support with automatic fallback to mock data.
- Basket strategy modes:
  - Cheapest mixed basket
  - Cheapest single-store basket
  - Best convenience option
- Preference and constraint controls:
  - Brand preference (neutral / own-brand preferred / branded preferred / branded only)
  - Avoid premium products
  - Organic-only filter
  - Max stores constraint (auto, 1, or 2)
- Premium decision-focused results:
  - Strategy cards with selected-strategy highlighting
  - Store-grouped purchase plan with per-item confidence and decision reasons
  - Savings + convenience trade-off summaries
  - Missing-item guidance and close alternatives
- MVVM architecture (`Models`, `ViewModels`, `Services`, `Views`).


## Stage 5 premium performance + visual polish

This milestone focused on *felt quality*: speed, responsiveness, hierarchy, and delight.

### What feels faster

- Debounced live search/autocomplete in the Add Item flow, with local-first progressive suggestions.
- Search suggestion caching (live + local ranked suggestions) to make repeated queries instant.
- Async comparison execution off the main thread to keep UI responsive during compare flows.
- Recent basket comparison result caching so reruns with same inputs return immediately.
- Reduced repeated computation in Results view model by precomputing purchase-plan groupings once.

### What looks and feels more premium

- Skeleton/shimmer loading rows for suggestion loading.
- Progressive loading messages (“Searching…”, “Local matches ready”, “Live suggestions ready”).
- Subtle haptics for add item, run comparison, save basket, and opening best-option results.
- Refined results hierarchy with animated total reveal, stronger strategy chips, and staged section reveal.
- Saved baskets and home surfaces refined with stronger badges/chips and subtle entrance animation.

### UX reliability and fallback tone

- Offline/live suggestion transitions now communicate status in user-friendly language.
- Compare flow now shows explicit progress phase text rather than a static spinner.

## Live vs mock data selection

The app chooses a data source at launch in `AppCoordinatorViewModel`:

1. If `LIVE_SUPERMARKET_DATA_URL` is **not** set, the app uses `MockSupermarketDataService`.
2. If `LIVE_SUPERMARKET_DATA_URL` is set, the app tries `LiveSupermarketDataService`.
3. If live fetch/decode succeeds with at least one supermarket, the app uses **LIVE** data.
4. If live fetch/decode fails, the app enters **live failed fallback** mode and explicitly switches to **MOCK**.

### Data source indicator in UI

The app now shows a visible badge:

- `LIVE DATA`
- `MOCK DATA`
- `LIVE FAILED → USING MOCK`

You can also open **Data Source Debug** from Home to inspect:

- active mode
- configured live URL
- live success/failure state
- last error
- supermarket count loaded
- last load timestamp
- backend debug marker

## Live data setup

Set an environment variable in your Xcode Run scheme:

- `LIVE_SUPERMARKET_DATA_URL=http://localhost:8000/catalog`

The Swift decoder expects `products[].category` to be one of these exact raw values:
`milk`, `bread`, `eggs`, `butter`, `pasta`, `bakedBeans`, `bananas`, `chickenBreast`, `cereal`, `cheese`, `tomatoes`, `rice`, `yogurt`, `apples`, `unknown`.

The `/catalog` response includes `metadata.debugMarker` so you can verify live payloads are being used (`LIVE_CATALOG_V3_MATCHING_INTELLIGENCE`).

Example payload shape:

```json
{
  "supermarkets": [
    {
      "name": "Tesco",
      "description": "...",
      "products": [
        {
          "name": "Tesco British Semi Skimmed Milk",
          "category": "milk",
          "subcategory": "milk",
          "price": 1.55,
          "size": "2L",
          "brand": "Tesco",
          "isOwnBrand": true,
          "isPremium": false,
          "isOrganic": false,
          "unitDescription": "per litre",
          "unitValue": 0.775,
          "tags": ["milk", "semi skimmed", "daily staple"]
        }
      ]
    }
  ],
  "metadata": {
    "source": "backend.catalog",
    "debugMarker": "LIVE_CATALOG_V3_MATCHING_INTELLIGENCE",
    "generatedAt": "2026-04-01T00:00:00Z"
  }
}
```

## Safe live-mode testing checklist

1. Start backend locally (`backend/README.md` has commands).
2. Set `LIVE_SUPERMARKET_DATA_URL` in the scheme.
3. Run app and verify badge shows `LIVE DATA`.
4. Open **Data Source Debug** and confirm marker `LIVE_CATALOG_V3_MATCHING_INTELLIGENCE`.
5. Stop backend (or break URL), relaunch app, and verify badge shows `LIVE FAILED → USING MOCK` plus the captured error.

## Project structure

- `UKSupermarketCompare.xcodeproj`
- `UKSupermarketCompare/UKSupermarketCompareApp.swift`
- `UKSupermarketCompare/Models`
- `UKSupermarketCompare/ViewModels`
- `UKSupermarketCompare/Services`
- `UKSupermarketCompare/Views`
- `backend/`

## Backend diagnostics (Stage 3 Step 5)

For live catalog/search health checks, use:

- `GET /diagnostics/catalog`
- `GET /diagnostics/search`

See `backend/README.md` for troubleshooting and validation steps.

## Stage 4 strategy model support

`POST /compare` now returns decision-oriented strategy results so the app can explain *why* a basket was chosen, not just the total.

Backend strategy payloads include these modes and metadata:

- total price + stores used/store count
- savings vs key alternatives
- missing-item summary
- chosen purchase-plan items (requested item, selected product/store, quantity, price, explanation, match confidence when available)
- human-readable explanation and trade-off summary.

This extends compare payloads while preserving `/catalog` contract compatibility and current live catalog data flow.


## Backend live data milestone

See `backend/README.md` for live Tesco provider configuration, import commands, API endpoints (`/autocomplete`, `/search`, `/product/{id}`, `/compare`, `/catalog`), and follow-up work for ASDA/Sainsbury's.
