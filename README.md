# UK Supermarket Compare (iOS SwiftUI)

This repository contains a native iPhone app built with Swift and SwiftUI, plus a FastAPI backend that can serve a live supermarket catalog.

## Open in Xcode

1. Open `UKSupermarketCompare.xcodeproj` in Xcode 16+.
2. Select an iPhone simulator (e.g., iPhone 16).
3. Build and run.

## App MVP features

- Welcome / Home screen
- Create Shopping List screen
- Supermarket Selection screen
- Basket Comparison Results screen
- Saved Lists screen
- Local persistence of saved lists via `UserDefaults`
- MVVM architecture (`Models`, `ViewModels`, `Services`, `Views`)

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

The Swift decoder expects supermarket/product keys exactly as today; it safely ignores extra fields.
The backend now includes a metadata marker (`LIVE_CATALOG_V1`) in `/catalog` responses so you can prove live data is being served.

## Safe live-mode testing checklist

1. Start backend locally (`backend/README.md` has commands).
2. Set `LIVE_SUPERMARKET_DATA_URL` in the scheme.
3. Run app and verify badge shows `LIVE DATA`.
4. Open **Data Source Debug** and confirm marker `LIVE_CATALOG_V1`.
5. Stop backend (or break URL), relaunch app, and verify badge shows `LIVE FAILED → USING MOCK` plus the captured error.

## Project structure

- `UKSupermarketCompare.xcodeproj`
- `UKSupermarketCompare/UKSupermarketCompareApp.swift`
- `UKSupermarketCompare/Models`
- `UKSupermarketCompare/ViewModels`
- `UKSupermarketCompare/Services`
- `UKSupermarketCompare/Views`
- `backend/`
