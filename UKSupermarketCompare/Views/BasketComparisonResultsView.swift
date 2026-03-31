import SwiftUI

struct BasketComparisonResultsView: View {
    @ObservedObject var viewModel: BasketComparisonResultsViewModel
    @State private var didSave = false

    var body: some View {
        List {
            summarySection
            supermarketTotalsSection
            mixedBasketSection
            unavailableSection
            saveSection
        }
        .listStyle(.insetGrouped)
        .navigationTitle("Optimised Basket")
    }

    private var summarySection: some View {
        Section("Summary") {
            summaryCard(
                title: "Cheapest mixed basket",
                value: viewModel.result.mixedBasket.total,
                tint: .green,
                subtitle: "Across \(viewModel.result.mixedBasket.supermarketsUsed.count) supermarkets"
            )

            if let cheapestSingle = viewModel.result.cheapestSingleStore {
                summaryCard(
                    title: "Cheapest single-store basket",
                    value: cheapestSingle.total,
                    tint: .blue,
                    subtitle: cheapestSingle.supermarket.name
                )
            } else {
                Text("No single supermarket could fulfil every intent.")
                    .foregroundStyle(.secondary)
            }

            summaryCard(
                title: "Savings vs most expensive",
                value: viewModel.result.savingsVsMostExpensive,
                tint: .purple,
                subtitle: "Based on selected supermarkets"
            )

            if viewModel.result.cheapestSingleStore != nil {
                summaryCard(
                    title: "Savings vs best single-store",
                    value: viewModel.result.savingsVsCheapestSingleStore,
                    tint: .orange,
                    subtitle: "Mixed basket advantage"
                )
            }
        }
    }

    private var supermarketTotalsSection: some View {
        Section("Supermarket totals") {
            ForEach(Array(viewModel.result.supermarketTotals.enumerated()), id: \.element.id) { index, total in
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("#\(index + 1) \(total.supermarket.name)")
                            .font(.headline)
                        Spacer()
                        Text(total.total, format: .currency(code: "GBP"))
                            .font(.headline)
                    }

                    if isCheapestSingleStore(total) {
                        badge("Best single-store")
                    }

                    if !total.unavailableItems.isEmpty {
                        Text("Missing \(total.unavailableItems.count) item(s)")
                            .font(.caption)
                            .foregroundStyle(.orange)
                    }
                }
                .padding(.vertical, 4)
            }
        }
    }

    private var mixedBasketSection: some View {
        Section("Cheapest mixed basket") {
            if viewModel.result.mixedBasket.selections.isEmpty {
                Text("No valid product matches were found for this basket.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(viewModel.result.mixedBasket.selections) { selection in
                    VStack(alignment: .leading, spacing: 8) {
                        Text("\(selection.intent.userInput) → \(selection.supermarket.name)")
                            .font(.subheadline.weight(.semibold))
                        Text(selection.product.name)
                            .font(.body)
                        HStack {
                            Text(selection.product.size)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text(selection.totalPrice, format: .currency(code: "GBP"))
                                .fontWeight(.semibold)
                        }

                        HStack(spacing: 8) {
                            badge(selection.product.isOwnBrand ? "Own Brand" : "Branded")
                            badge(selection.matchQuality.label)
                            if selection.product.isPremium {
                                badge("Premium")
                            }
                        }
                    }
                    .padding(.vertical, 4)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Divider()
                    Text("Mixed total: \(viewModel.result.mixedBasket.total, format: .currency(code: "GBP"))")
                        .font(.headline)
                    Text("Uses \(viewModel.result.mixedBasket.supermarketsUsed.count) supermarket(s)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.top, 8)
            }
        }
    }

    private var unavailableSection: some View {
        Section("Fallback") {
            if viewModel.result.mixedBasket.unavailableItems.isEmpty {
                Text("All intents matched successfully.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(viewModel.result.mixedBasket.unavailableItems) { intent in
                    Text("No sensible match found for \(intent.userInput).")
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private var saveSection: some View {
        Section {
            Button(didSave ? "Saved" : "Save List") {
                viewModel.saveList()
                didSave = true
            }
            .disabled(didSave)
        }
    }

    private func summaryCard(title: String, value: Decimal, tint: Color, subtitle: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Text(value, format: .currency(code: "GBP"))
                .font(.title3.weight(.bold))
                .foregroundStyle(tint)
            Text(subtitle)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 6)
    }

    private func badge(_ label: String) -> some View {
        Text(label)
            .font(.caption2.weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color(.secondarySystemBackground))
            .clipShape(Capsule())
    }

    private func isCheapestSingleStore(_ total: SupermarketBasketTotal) -> Bool {
        viewModel.result.cheapestSingleStore?.supermarket.id == total.supermarket.id
    }
}
