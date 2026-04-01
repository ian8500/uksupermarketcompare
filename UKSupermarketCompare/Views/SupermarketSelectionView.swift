import SwiftUI

struct SupermarketSelectionView: View {
    @ObservedObject var viewModel: SupermarketSelectionViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                BrandHeader(title: "Choose supermarkets", subtitle: "Pick stores and comparison preferences.")

                BrandCard {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Basket mode")
                            .font(BrandTypography.caption)
                            .foregroundStyle(BrandPalette.textSecondary)
                        Picker("Basket mode", selection: $viewModel.comparisonMode) {
                            ForEach(BasketComparisonMode.allCases, id: \.self) { mode in
                                Text(mode.title).tag(mode)
                            }
                        }
                        .pickerStyle(.segmented)
                    }
                }

                BrandCard {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Preferences")
                            .font(BrandTypography.caption)
                            .foregroundStyle(BrandPalette.textSecondary)
                        Picker("Brand", selection: $viewModel.brandPreference) {
                            ForEach(BrandPreference.allCases, id: \.self) { preference in
                                Text(preference.title).tag(preference)
                            }
                        }

                        Toggle("Avoid premium", isOn: $viewModel.avoidPremium)
                        Toggle("Organic only", isOn: $viewModel.organicOnly)

                        Picker("Max stores", selection: $viewModel.maxStores) {
                            Text("Auto").tag(0)
                            Text("1 store").tag(1)
                            Text("2 stores").tag(2)
                        }
                        .pickerStyle(.segmented)
                    }
                }

                ForEach(viewModel.supermarkets) { market in
                    Button { viewModel.toggleSelection(for: market) } label: {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(market.name).font(BrandTypography.section)
                                Text(market.description)
                                    .font(BrandTypography.caption)
                                    .foregroundStyle(BrandPalette.textSecondary)
                            }
                            Spacer()
                            Image(systemName: viewModel.selectedMarketIDs.contains(market.id) ? "checkmark.circle.fill" : "circle")
                                .foregroundStyle(viewModel.selectedMarketIDs.contains(market.id) ? BrandPalette.red : BrandPalette.textSecondary)
                        }
                    }
                    .buttonStyle(.plain)
                    .padding(2)
                    .background(BrandPalette.cloud.opacity(0.7))
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                }
                .padding(.horizontal, 8)

                Button("Compare basket") { viewModel.runComparison() }
                    .buttonStyle(BrandPrimaryButtonStyle())
                    .disabled(!viewModel.canCompare)
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Supermarkets")
    }
}
