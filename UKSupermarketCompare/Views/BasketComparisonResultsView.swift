import SwiftUI

struct BasketComparisonResultsView: View {
    @ObservedObject var viewModel: BasketComparisonResultsViewModel
    @State private var didSave = false

    var body: some View {
        List {
            summarySection
            supermarketTotalsSection
            selectedBasketSection
            unavailableSection
            saveSection
        }
        .listStyle(.insetGrouped)
        .navigationTitle("Optimised Basket")
    }

    private var summarySection: some View {
        Section("Summary") {
            summaryCard(
                title: "Selected strategy",
                value: viewModel.result.selectedBasket.total,
                tint: .green,
                subtitle: viewModel.result.comparisonMode.title
            )

            if let cheapestSingle = viewModel.result.cheapestSingleStore {
                summaryCard(
                    title: "Cheapest single-store basket",
                    value: cheapestSingle.total,
                    tint: .blue,
                    subtitle: cheapestSingle.supermarket.name
                )
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
                    subtitle: "Strategy advantage"
                )
            }
        }
    }

    private var supermarketTotalsSection: some View {
        Section("Supermarket totals") {
            ForEach(Array(viewModel.result.supermarketTotals.enumerated()), id: \.element.id) { index, total in
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Label(total.supermarket.name, systemImage: "cart")
                            .font(.headline)
                        Spacer()
                        Text(total.total, format: .currency(code: "GBP"))
                            .font(.headline)
                    }

                    if isCheapestSingleStore(total) {
                        badge("Best single-store", tint: .blue)
                    }

                    if !total.unavailableItems.isEmpty {
                        Text("Missing \(total.unavailableItems.count) item(s)")
                            .font(.caption)
                            .foregroundStyle(.orange)
                    }

                    Text("Rank #\(index + 1)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
    }

    private var selectedBasketSection: some View {
        Section(viewModel.result.comparisonMode == .cheapestPossible ? "Cheapest mixed basket" : "Cheapest single-store basket") {
            if viewModel.result.selectedBasket.selections.isEmpty {
                Text("No valid product matches were found for this basket.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(viewModel.result.selectedBasket.selections) { selection in
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("\(selection.intent.quantity)x \(selection.intent.userInput)")
                                .font(.subheadline.weight(.semibold))
                            Spacer()
                            Text(selection.totalPrice, format: .currency(code: "GBP"))
                                .fontWeight(.semibold)
                        }

                        Text(selection.product.name)
                            .font(.body)

                        HStack {
                            Text("\(selection.supermarket.name) • \(selection.product.size)")
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text("\(selection.product.unitDescription): \(selection.product.unitValue, format: .currency(code: "GBP"))")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }

                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                badge(selection.product.isOwnBrand ? "Own-brand" : selection.product.brand, tint: .gray)
                                badge(selection.matchQuality.label, tint: .green)
                                if selection.product.isPremium {
                                    badge("Premium", tint: .purple)
                                }
                                if selection.product.isOrganic {
                                    badge("Organic", tint: .mint)
                                }
                                badge(selection.supermarket.name, tint: .blue)
                            }
                        }

                        VStack(alignment: .leading, spacing: 4) {
                            Text("Why selected")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(.secondary)
                            ForEach(selection.reasons, id: \.self) { reason in
                                Text("• \(reason)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .padding(.vertical, 6)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Divider()
                    Text("Total: \(viewModel.result.selectedBasket.total, format: .currency(code: "GBP"))")
                        .font(.headline)
                    Text("Uses \(viewModel.result.selectedBasket.supermarketsUsed.count) supermarket(s)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.top, 8)
            }
        }
    }

    private var unavailableSection: some View {
        Section("Fallback") {
            if viewModel.result.selectedBasket.unavailableItems.isEmpty {
                Text("All intents matched successfully.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(viewModel.result.selectedBasket.unavailableItems) { intent in
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

    private func badge(_ label: String, tint: Color) -> some View {
        Text(label)
            .font(.caption2.weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(tint.opacity(0.12))
            .foregroundStyle(tint)
            .clipShape(Capsule())
    }

    private func isCheapestSingleStore(_ total: SupermarketBasketTotal) -> Bool {
        viewModel.result.cheapestSingleStore?.supermarket.id == total.supermarket.id
    }
}
