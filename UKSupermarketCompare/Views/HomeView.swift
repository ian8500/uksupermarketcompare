import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: HomeViewModel
    @State private var showDataSourceDebug = false
    @State private var animateHero = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BrandMetrics.spacingMD) {
                BrandLogoView(subtitle: "Your grocery savings co-pilot")
                    .padding(.top, 8)
                    .scaleEffect(animateHero ? 1 : 0.98)
                    .opacity(animateHero ? 1 : 0.85)

                DataSourceBadgeView(status: coordinator.dataSourceStatus)

                BrandCard {
                    VStack(alignment: .leading, spacing: BrandMetrics.spacingSM) {
                        Text(viewModel.title)
                            .font(BrandTypography.display)
                            .foregroundStyle(BrandPalette.textPrimary)
                            .lineLimit(2)
                        Text(viewModel.subtitle)
                            .font(BrandTypography.body)
                            .foregroundStyle(BrandPalette.textSecondary)

                        HStack(spacing: 8) {
                            BrandChip(text: "Live basket planning", tint: BrandPalette.blue)
                            BrandChip(text: "Store-by-store totals", tint: BrandPalette.red)
                            BrandChip(text: "Faster search", tint: BrandPalette.success)
                        }
                    }
                }

                savingsCalloutCard

                BrandCard {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Get started")
                            .font(BrandTypography.section)
                            .foregroundStyle(BrandPalette.navy)

                        Button("Create Shopping List") {
                            coordinator.openCreateList()
                            HapticFeedbackService.tap()
                        }
                        .buttonStyle(BrandPrimaryButtonStyle())

                        Button("View Saved Lists") {
                            coordinator.openSavedLists()
                            HapticFeedbackService.tap()
                        }
                        .buttonStyle(BrandSecondaryButtonStyle())

                        if let lastBasket = coordinator.store.lastBasket {
                            Button("Rerun last basket (\(lastBasket.items.count) items)") {
                                coordinator.openSelection(for: lastBasket)
                                HapticFeedbackService.tap()
                            }
                            .buttonStyle(BrandSecondaryButtonStyle())
                        }
                    }
                }

                BrandCard {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Weekly momentum")
                            .font(BrandTypography.section)
                            .foregroundStyle(BrandPalette.navy)
                        HStack(spacing: 8) {
                            BrandChip(text: "\(coordinator.store.savedLists.count) saved baskets", tint: BrandPalette.blue)
                            BrandChip(text: "\(coordinator.store.favoriteItems.count) favorites", tint: BrandPalette.red)
                        }
                        Text("Use rerun + favorites to finish your weekly shop setup faster each time.")
                            .font(BrandTypography.caption)
                            .foregroundStyle(BrandPalette.textSecondary)
                    }
                }

                BrandCard {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Developer debug")
                            .font(BrandTypography.section)
                            .foregroundStyle(BrandPalette.navy)
                        Text("Check whether the app is currently using live backend data or mock fallback data.")
                            .font(BrandTypography.body)
                            .foregroundStyle(BrandPalette.textSecondary)

                        Button("Open Data Source Debug") {
                            showDataSourceDebug = true
                        }
                        .buttonStyle(BrandSecondaryButtonStyle())
                    }
                }

                BrandCard {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("How it works")
                            .font(BrandTypography.section)
                            .foregroundStyle(BrandPalette.navy)
                        Text("1. Add groceries. 2. Pick your supermarkets. 3. Compare total cost instantly.")
                            .font(BrandTypography.body)
                            .foregroundStyle(BrandPalette.textSecondary)
                    }
                }
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Welcome")
        .onAppear {
            withAnimation(.easeOut(duration: 0.35)) {
                animateHero = true
            }
        }
        .sheet(isPresented: $showDataSourceDebug) {
            NavigationStack {
                DataSourceDebugView(status: coordinator.dataSourceStatus)
            }
        }
    }

    private var savingsCalloutCard: some View {
        VStack(alignment: .leading, spacing: BrandMetrics.spacingSM) {
            Text("Save £10–£20 per week")
                .font(BrandTypography.title.weight(.bold))
                .foregroundStyle(.white)
            Text("Most households unlock savings by mixing stores and rerunning the same basket weekly.")
                .font(BrandTypography.body)
                .foregroundStyle(.white.opacity(0.92))
            BrandBadge(text: "Typical weekly range", tint: .white)
                .foregroundStyle(BrandPalette.navy)
        }
        .padding(BrandMetrics.spacingLG)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: BrandMetrics.cardRadius, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [BrandPalette.blue, BrandPalette.red],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
        )
        .shadow(color: BrandPalette.blue.opacity(0.22), radius: 14, y: 8)
    }
}
