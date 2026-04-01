import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: HomeViewModel
    @State private var showDataSourceDebug = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                BrandLogoView(subtitle: "Your grocery savings co-pilot")
                    .padding(.top, 8)

                DataSourceBadgeView(status: coordinator.dataSourceStatus)

                BrandCard {
                    VStack(alignment: .leading, spacing: 10) {
                        Text(viewModel.title)
                            .font(BrandTypography.hero)
                            .foregroundStyle(BrandPalette.textPrimary)
                        Text(viewModel.subtitle)
                            .font(BrandTypography.body)
                            .foregroundStyle(BrandPalette.textSecondary)

                        HStack(spacing: 8) {
                            BrandChip(text: "Live basket planning", tint: BrandPalette.blue)
                            BrandChip(text: "Store-by-store totals", tint: BrandPalette.red)
                        }
                    }
                }

                BrandCard {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Get started")
                            .font(BrandTypography.section)
                            .foregroundStyle(BrandPalette.navy)

                        Button("Create Shopping List") {
                            coordinator.openCreateList()
                        }
                        .buttonStyle(BrandPrimaryButtonStyle())

                        Button("View Saved Lists") {
                            coordinator.openSavedLists()
                        }
                        .buttonStyle(BrandSecondaryButtonStyle())
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
        .sheet(isPresented: $showDataSourceDebug) {
            NavigationStack {
                DataSourceDebugView(status: coordinator.dataSourceStatus)
            }
        }
    }
}
