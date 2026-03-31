import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: HomeViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.lg) {
                HStack {
                    AppWordmark()
                    Spacer()
                    AppBadge(text: "Beta", tint: AppColors.brandBlue)
                }

                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text(viewModel.title)
                        .font(AppTypography.hero)
                        .foregroundStyle(AppColors.textPrimary)
                    Text(viewModel.subtitle)
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textSecondary)
                }

                VStack(spacing: AppSpacing.md) {
                    Button("Create New List") { coordinator.openCreateList() }
                        .buttonStyle(AppPrimaryButtonStyle())
                    Button("Saved Lists") { coordinator.openSavedLists() }
                        .buttonStyle(.bordered)
                        .tint(AppColors.brandBlue)
                    Button("Sample Comparison") { coordinator.openCreateList() }
                        .buttonStyle(.bordered)
                        .tint(AppColors.brandRed)
                }

                AppSectionHeader(
                    title: "How it works",
                    subtitle: "Add groceries, select supermarkets, and get the lowest basket strategy in seconds."
                )
                .appCardStyle()

                AppEmptyState(
                    icon: "basket",
                    title: "Ready for your weekly shop?",
                    subtitle: "Build a list and compare mock prices from major UK supermarkets."
                )
            }
            .padding(AppSpacing.md)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Welcome")
    }
}
