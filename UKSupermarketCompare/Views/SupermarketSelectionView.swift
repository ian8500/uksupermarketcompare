import SwiftUI

struct SupermarketSelectionView: View {
    @ObservedObject var viewModel: SupermarketSelectionViewModel

    var body: some View {
        List {
            Section("Compare mode") {
                Picker("Basket mode", selection: $viewModel.comparisonMode) {
                    ForEach(BasketComparisonMode.allCases, id: \.self) { mode in
                        Text(mode.title).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
            }

            Section("Product preferences") {
                Picker("Brand", selection: $viewModel.brandPreference) {
                    ForEach(BrandPreference.allCases, id: \.self) { preference in
                        Text(preference.title).tag(preference)
                    }
                }
                Toggle("Avoid premium", isOn: $viewModel.avoidPremium)
                Toggle("Organic only", isOn: $viewModel.organicOnly)
            }

            Section("Choose supermarkets") {
                ForEach(viewModel.supermarkets) { market in
                    Button {
                        viewModel.toggleSelection(for: market)
                    } label: {
                        HStack {
                            VStack(alignment: .leading) {
                                Text(market.name)
                                    .font(.headline)
                                Text(market.description)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Image(systemName: viewModel.selectedMarketIDs.contains(market.id) ? "checkmark.circle.fill" : "circle")
                                .foregroundStyle(viewModel.selectedMarketIDs.contains(market.id) ? .green : .gray)
                        }
                    }
                    .buttonStyle(.plain)
                }
            }

            Section {
                Button("Compare Basket") {
                    viewModel.runComparison()
                }
                .buttonStyle(.borderedProminent)
                .disabled(!viewModel.canCompare)
            }
        }
        .navigationTitle("Supermarket Selection")
    }
}
