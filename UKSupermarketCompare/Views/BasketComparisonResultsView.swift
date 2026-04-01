import SwiftUI

struct BasketComparisonResultsView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: BasketComparisonResultsViewModel
    @State private var didSave = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                BrandHeader(title: "Optimised basket", subtitle: "Fast overview of your lowest-cost outcome.")
                DataSourceBadgeView(status: coordinator.dataSourceStatus)

                section("Summary") {
                    summaryCard(
                        title: "Selected strategy",
                        value: viewModel.result.selectedBasket.total,
                        tint: BrandPalette.success,
                        subtitle: viewModel.result.comparisonMode.title
                    )

                    if let cheapestSingle = viewModel.result.cheapestSingleStore {
                        summaryCard(
                            title: "Cheapest single-store",
                            value: cheapestSingle.total,
                            tint: BrandPalette.blue,
                            subtitle: cheapestSingle.supermarket.name
                        )
                    }

                    summaryCard(
                        title: "Savings vs highest",
                        value: viewModel.result.savingsVsMostExpensive,
                        tint: BrandPalette.red,
                        subtitle: "Across selected supermarkets"
                    )

                    summaryCard(
                        title: "Savings vs single-store",
                        value: viewModel.result.savingsVsCheapestSingleStore,
                        tint: BrandPalette.success,
                        subtitle: "How much mixed basket saves"
                    )

                    if let convenience = viewModel.bestConvenienceOption {
                        summaryCard(
                            title: "Best convenience option",
                            value: convenience.total,
                            tint: BrandPalette.navy,
                            subtitle: "\(convenience.supermarket.name) • \(convenience.unavailableItems.count) missing"
                        )
                    }

                    BrandCard {
                        Text(viewModel.savingsExplanation)
                            .font(BrandTypography.body)
                            .foregroundStyle(BrandPalette.textSecondary)
                    }
                }

                section("Supermarket totals") {
                    ForEach(Array(viewModel.result.supermarketTotals.enumerated()), id: \.element.id) { index, total in
                        BrandCard {
                            HStack(alignment: .top) {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text(total.supermarket.name)
                                        .font(BrandTypography.section)
                                    HStack(spacing: 8) {
                                        if isCheapestSingleStore(total) {
                                            BrandBadge(text: "Best single-store")
                                        }
                                        if !total.unavailableItems.isEmpty {
                                            BrandBadge(text: "Missing \(total.unavailableItems.count)", tint: BrandPalette.warning)
                                        }
                                    }
                                }
                                Spacer()
                                VStack(alignment: .trailing, spacing: 6) {
                                    Text(total.total, format: .currency(code: "GBP"))
                                        .font(BrandTypography.section)
                                    BrandChip(text: "Rank #\(index + 1)", tint: BrandPalette.red)
                                }
                            }
                        }
                    }
                }

                section(viewModel.result.comparisonMode == .cheapestPossible ? "Selected products" : "Selected single-store products") {
                    if viewModel.result.selectedBasket.selections.isEmpty {
                        BrandCard {
                            Text("No valid product matches were found for this basket.")
                                .foregroundStyle(BrandPalette.textSecondary)
                        }
                    } else {
                        ForEach(viewModel.result.selectedBasket.selections) { selection in
                            BrandCard {
                                VStack(alignment: .leading, spacing: 10) {
                                    HStack(alignment: .top) {
                                        VStack(alignment: .leading, spacing: 4) {
                                            Text("\(selection.intent.quantity)x \(selection.intent.userInput)")
                                                .font(BrandTypography.section)
                                            Text("\(selection.supermarket.name) • \(selection.product.size)")
                                                .font(BrandTypography.caption)
                                                .foregroundStyle(BrandPalette.textSecondary)
                                        }
                                        Spacer()
                                        Text(selection.totalPrice, format: .currency(code: "GBP"))
                                            .font(BrandTypography.section)
                                            .foregroundStyle(BrandPalette.blue)
                                    }

                                    Text(selection.product.name)
                                        .font(BrandTypography.body)

                                    ScrollView(.horizontal, showsIndicators: false) {
                                        HStack(spacing: 8) {
                                            BrandBadge(text: selection.product.isOwnBrand ? "Own-brand" : selection.product.brand, tint: BrandPalette.textSecondary)
                                            BrandBadge(text: selection.matchQuality.label, tint: BrandPalette.success)
                                            if selection.product.isPremium {
                                                BrandBadge(text: "Premium", tint: BrandPalette.red)
                                            }
                                            if selection.product.isOrganic {
                                                BrandBadge(text: "Organic", tint: BrandPalette.success)
                                            }
                                        }
                                    }

                                    VStack(alignment: .leading, spacing: 4) {
                                        ForEach(Array(selection.reasons.prefix(3).enumerated()), id: \.offset) { _, reason in
                                            Text("• \(reason)")
                                                .font(BrandTypography.caption)
                                                .foregroundStyle(BrandPalette.textSecondary)
                                        }
                                        Text("Debug score: \(selection.confidence.description) • \(selection.unitPriceDescription)")
                                            .font(BrandTypography.caption)
                                            .foregroundStyle(BrandPalette.textSecondary)
                                    }
                                }
                            }
                        }
                    }
                }

                section("Unmatched items") {
                    BrandCard {
                        Text(viewModel.result.selectedBasket.missingItemsExplanation)
                            .font(BrandTypography.body)
                            .foregroundStyle(viewModel.result.selectedBasket.unavailableItems.isEmpty ? BrandPalette.success : BrandPalette.textSecondary)
                    }

                    if !viewModel.result.selectedBasket.unavailableItems.isEmpty {
                        ForEach(viewModel.result.selectedBasket.unavailableItems) { intent in
                            BrandCard {
                                Text("No sensible match found for \(intent.userInput). Try adding a category hint like milk, bread, or rice.")
                                    .font(BrandTypography.body)
                                    .foregroundStyle(BrandPalette.textSecondary)
                            }
                        }
                    }
                }

                Button(didSave ? "Saved" : "Save List") {
                    viewModel.saveList()
                    didSave = true
                }
                .buttonStyle(BrandPrimaryButtonStyle())
                .disabled(didSave)
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Results")
    }

    private func section<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(BrandTypography.section)
                .foregroundStyle(BrandPalette.navy)
            content()
        }
    }

    private func summaryCard(title: String, value: Decimal, tint: Color, subtitle: String) -> some View {
        BrandCard {
            VStack(alignment: .leading, spacing: 6) {
                Text(title)
                    .font(BrandTypography.caption)
                    .foregroundStyle(BrandPalette.textSecondary)
                Text(value, format: .currency(code: "GBP"))
                    .font(BrandTypography.title)
                    .foregroundStyle(tint)
                Text(subtitle)
                    .font(BrandTypography.caption)
                    .foregroundStyle(BrandPalette.textSecondary)
            }
        }
    }

    private func isCheapestSingleStore(_ total: SupermarketBasketTotal) -> Bool {
        viewModel.result.cheapestSingleStore?.supermarket.id == total.supermarket.id
    }
}
