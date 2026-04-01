import Foundation

enum AppDataSourceMode: String {
    case live
    case mock
    case liveFailedFallback

    var badgeTitle: String {
        switch self {
        case .live:
            return "LIVE DATA"
        case .mock:
            return "MOCK DATA"
        case .liveFailedFallback:
            return "LIVE FAILED → USING MOCK"
        }
    }
}

struct AppDataSourceStatus {
    let mode: AppDataSourceMode
    let liveURL: URL?
    let lastLiveLoadError: String?
    let supermarketCount: Int
    let lastLoadAt: Date
    let backendMarker: String?

    var lastLiveLoadSucceeded: Bool {
        mode == .live
    }

    static func mock(liveURL: URL?, error: String? = nil, marker: String? = nil, supermarketCount: Int) -> AppDataSourceStatus {
        AppDataSourceStatus(
            mode: error == nil ? .mock : .liveFailedFallback,
            liveURL: liveURL,
            lastLiveLoadError: error,
            supermarketCount: supermarketCount,
            lastLoadAt: Date(),
            backendMarker: marker
        )
    }
}
