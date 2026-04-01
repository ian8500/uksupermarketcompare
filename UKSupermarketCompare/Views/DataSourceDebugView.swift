import SwiftUI

struct DataSourceBadgeView: View {
    let status: AppDataSourceStatus

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            Text(status.mode.badgeTitle)
                .font(BrandTypography.caption.weight(.semibold))
                .foregroundStyle(color)
            if let marker = status.backendMarker, !marker.isEmpty {
                Text(marker)
                    .font(BrandTypography.caption)
                    .foregroundStyle(BrandPalette.textSecondary)
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(color.opacity(0.12), in: Capsule())
    }

    private var color: Color {
        switch status.mode {
        case .live: return BrandPalette.success
        case .mock: return BrandPalette.warning
        case .liveFailedFallback: return BrandPalette.red
        }
    }
}

struct DataSourceDebugView: View {
    let status: AppDataSourceStatus

    var body: some View {
        List {
            section("Mode", value: status.mode.badgeTitle)
            section("Live URL", value: status.liveURL?.absoluteString ?? "Not configured")
            section("Last live load", value: status.lastLiveLoadSucceeded ? "Success" : "Not successful")
            section("Loaded supermarkets", value: "\(status.supermarketCount)")
            section("Backend marker", value: status.backendMarker ?? "None")
            section("Last load timestamp", value: status.lastLoadAt.formatted(date: .abbreviated, time: .standard))
            section("Last live error", value: status.lastLiveLoadError ?? "None")
        }
        .navigationTitle("Data Source Debug")
    }

    private func section(_ title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(BrandTypography.caption)
                .foregroundStyle(BrandPalette.textSecondary)
            Text(value)
                .font(BrandTypography.body)
                .foregroundStyle(BrandPalette.textPrimary)
        }
        .padding(.vertical, 4)
    }
}
