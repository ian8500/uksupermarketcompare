# UK Supermarket Compare (iOS SwiftUI)

This repository now contains a native iPhone app built with Swift and SwiftUI.

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
- Mock UK supermarket data service
- Local persistence of saved lists via `UserDefaults`
- MVVM architecture (`Models`, `ViewModels`, `Services`, `Views`)

## Project structure

- `UKSupermarketCompare.xcodeproj`
- `UKSupermarketCompare/UKSupermarketCompareApp.swift`
- `UKSupermarketCompare/Models`
- `UKSupermarketCompare/ViewModels`
- `UKSupermarketCompare/Services`
- `UKSupermarketCompare/Views`

## Live data setup

By default the app still falls back to mock supermarket data. To use live data, set an environment variable in your Xcode Run scheme:

- `LIVE_SUPERMARKET_DATA_URL=http://localhost:8000/catalog`

Expected JSON shape:

```json
{
  "supermarkets": [
    {
      "name": "Tesco",
      "description": "...",
      "products": [
        {
          "name": "Tesco Semi Skimmed Milk 2L",
          "category": "milk",
          "subcategory": "semi-skimmed",
          "price": 1.55,
          "size": "2L",
          "brand": "Tesco",
          "isOwnBrand": true,
          "isPremium": false,
          "isOrganic": false,
          "unitDescription": "per litre",
          "unitValue": 0.775,
          "tags": ["milk", "semi skimmed"]
        }
      ]
    }
  ]
}
```

If fetching/parsing fails, the app automatically falls back to `MockSupermarketDataService`.
