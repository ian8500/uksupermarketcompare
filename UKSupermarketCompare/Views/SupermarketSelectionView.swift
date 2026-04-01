import SwiftUI

struct SupermarketSelectionView: View {
    @ObservedObject var viewModel: SupermarketSelectionViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                BrandHeader(title: "Choose supermarkets", subtitle: "Pick stores and comparison preferences.")

                BrandCard {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Shopping strategy")
                            .font(BrandTypography.caption)
                            .foregroundStyle(BrandPalette.textSecondary)
                        VStack(alignment: .leading, spacing: 8) {
                            ForEach(viewModel.modeOptions) { option in
                                Button {
                                    viewModel.comparisonMode = option.mode
                                } label: {
                                    HStack(alignment: .top, spacing: 10) {
                                        Image(systemName: viewModel.comparisonMode == option.mode ? "largecircle.fill.circle" : "circle")
                                            .foregroundStyle(viewModel.comparisonMode == option.mode ? BrandPalette.red : BrandPalette.textSecondary)
                                        VStack(alignment: .leading, spacing: 2) {
                                            Text(option.mode.title)
                                                .font(BrandTypography.body.weight(.semibold))
                                                .foregroundStyle(BrandPalette.textPrimary)
                                            Text(option.mode.summary)
                                                .font(BrandTypography.caption)
                                                .foregroundStyle(BrandPalette.textSecondary)
                                        }
                                        Spacer()
                                    }
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                }

                BrandCard {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Shopping preferences")
                            .font(BrandTypography.caption)
                            .foregroundStyle(BrandPalette.textSecondary)
                        Picker("Brand", selection: $viewModel.brandPreference) {
                            ForEach(BrandPreference.allCases, id: \.self) { preference in
                                Text(preference.title).tag(preference)
                            }
                        }

                        Toggle("Avoid premium", isOn: $viewModel.avoidPremium)
                        Toggle("Organic only", isOn: $viewModel.organicOnly)
                        Text("Store limit for mixed baskets")
                            .font(BrandTypography.caption)
                            .foregroundStyle(BrandPalette.textSecondary)

                        Picker("Max stores", selection: $viewModel.maxStores) {
                            Text("Auto").tag(0)
                            Text("1 store").tag(1)
                            Text("2 stores").tag(2)
                        }
                        .pickerStyle(.segmented)

                        Text(viewModel.selectedModeSummary)
                            .font(BrandTypography.caption)
                            .foregroundStyle(BrandPalette.textSecondary)
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

                Button {
                    viewModel.runComparison()
                } label: {
                    HStack {
                        if viewModel.isComparing {
                            ProgressView()
                                .tint(.white)
                        }
                        Text(viewModel.isComparing ? "Comparing..." : "Compare basket")
                    }
                }
                    .buttonStyle(BrandPrimaryButtonStyle())
                    .disabled(!viewModel.canCompare || viewModel.isComparing)
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Supermarkets")
    }
}
