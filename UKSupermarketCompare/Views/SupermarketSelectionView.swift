import SwiftUI

struct SupermarketSelectionView: View {
    @ObservedObject var viewModel: SupermarketSelectionViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.md) {
                AppSectionHeader(title: "Choose supermarkets", subtitle: "Pick stores and comparison preferences.")

                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text("Basket mode").font(AppTypography.caption).foregroundStyle(AppColors.textSecondary)
                    Picker("Basket mode", selection: $viewModel.comparisonMode) {
                        ForEach(BasketComparisonMode.allCases, id: \.self) { mode in
                            Text(mode.title).tag(mode)
                        }
                    }
                    .pickerStyle(.segmented)
                }
                .appCardStyle()

                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text("Preferences").font(AppTypography.caption).foregroundStyle(AppColors.textSecondary)
                    Picker("Brand", selection: $viewModel.brandPreference) {
                        ForEach(BrandPreference.allCases, id: \.self) { preference in
                            Text(preference.title).tag(preference)
                        }
                    }
                    Toggle("Avoid premium", isOn: $viewModel.avoidPremium)
                    Toggle("Organic only", isOn: $viewModel.organicOnly)
                }
                .appCardStyle()

                ForEach(viewModel.supermarkets) { market in
                    Button { viewModel.toggleSelection(for: market) } label: {
                        HStack {
                            VStack(alignment: .leading) {
                                Text(market.name).font(.headline)
                                Text(market.description).font(.caption).foregroundStyle(AppColors.textSecondary)
                            }
                            Spacer()
                            Image(systemName: viewModel.selectedMarketIDs.contains(market.id) ? "checkmark.circle.fill" : "circle")
                                .foregroundStyle(viewModel.selectedMarketIDs.contains(market.id) ? AppColors.brandRed : .gray)
                        }
                    }
                    .buttonStyle(.plain)
                    .appCardStyle()
                }

                Button("Compare basket") { viewModel.runComparison() }
                    .buttonStyle(AppPrimaryButtonStyle())
                    .disabled(!viewModel.canCompare)
            }
            .padding(AppSpacing.md)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Supermarkets")
    }
}
