import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: HomeViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                BrandLogoView()
                    .padding(.top, 8)

                BrandCard {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(viewModel.title)
                            .font(BrandTypography.hero)
                            .foregroundStyle(BrandPalette.textPrimary)
                        Text(viewModel.subtitle)
                            .font(BrandTypography.body)
                            .foregroundStyle(BrandPalette.textSecondary)
                        HStack(spacing: 8) {
                            BrandBadge(text: "Groceries")
                            BrandBadge(text: "Price Compare", tint: BrandPalette.red)
                            BrandBadge(text: "Save Money", tint: BrandPalette.success)
                        }
                        .padding(.top, 4)
                    }
                }

                VStack(spacing: 12) {
                    Button("Create Shopping List") {
                        coordinator.openCreateList()
                    }
                    .buttonStyle(BrandPrimaryButtonStyle())

                    Button("View Saved Lists") {
                        coordinator.openSavedLists()
                    }
                    .buttonStyle(BrandSecondaryButtonStyle())
                }

                Spacer(minLength: 12)
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Welcome")
    }
}
