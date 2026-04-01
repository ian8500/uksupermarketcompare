import SwiftUI

struct BasketComparisonResultsView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: BasketComparisonResultsViewModel
    @State private var didSave = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                BrandHeader(title: "Premium basket decision", subtitle: "Clear outcomes, practical plan, confident checkout.")
                DataSourceBadgeView(status: coordinator.dataSourceStatus)

                section("Decision cards") {
                    decisionSummaryCards
                }

                if !viewModel.preferenceEffects.isEmpty {
                    section("Applied preferences") {
                        BrandCard {
                            VStack(alignment: .leading, spacing: 8) {
                                ForEach(viewModel.preferenceEffects, id: \.self) { effect in
                                    Text("• \(effect)")
                                        .font(BrandTypography.caption)
                                        .foregroundStyle(BrandPalette.textSecondary)
                                }
                            }
                        }
                    }
                }

                section("Purchase plan") {
                    if viewModel.purchasePlanByStore.isEmpty {
                        BrandCard {
                            Text("No practical purchase plan is available yet because no reliable matches were found.")
                                .font(BrandTypography.body)
                                .foregroundStyle(BrandPalette.textSecondary)
                        }
                    } else {
                        BrandCard {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Action plan")
                                    .font(BrandTypography.section)
                                    .foregroundStyle(BrandPalette.navy)
                                Text("Follow this store-by-store list to complete your basket quickly.")
                                    .font(BrandTypography.caption)
                                    .foregroundStyle(BrandPalette.textSecondary)
                            }
                        }

                        ForEach(viewModel.purchasePlanByStore, id: \.supermarket.id) { group in
                            BrandCard {
                                VStack(alignment: .leading, spacing: 10) {
                                    HStack {
                                        Text(group.supermarket.name)
                                            .font(BrandTypography.section)
                                        Spacer()
                                        Text(group.total.asGBP())
                                            .font(BrandTypography.section)
                                            .foregroundStyle(BrandPalette.blue)
                                    }

                                    ForEach(group.selections) { selection in
                                        HStack(alignment: .top) {
                                            VStack(alignment: .leading, spacing: 4) {
                                                Text("\(selection.quantity)x \(selection.product.name)")
                                                    .font(BrandTypography.body)
                                                Text(selection.intent.userInput)
                                                    .font(BrandTypography.caption)
                                                    .foregroundStyle(BrandPalette.textSecondary)
                                            }
                                            Spacer()
                                            Text(selection.totalPrice.asGBP())
                                                .font(BrandTypography.section)
                                                .foregroundStyle(BrandPalette.navy)
                                        }
                                        if selection.id != group.selections.last?.id {
                                            Divider()
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                section("Supermarket ranking") {
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
                                    Text(total.total.asGBP())
                                        .font(BrandTypography.section)
                                    BrandChip(text: "Rank #\(index + 1)", tint: BrandPalette.red)
                                    Text("\(total.selections.count) matched")
                                        .font(BrandTypography.caption)
                                        .foregroundStyle(BrandPalette.textSecondary)
                                }
                            }
                        }
                    }
                }

                section("Missing items and alternatives") {
                    BrandCard {
                        Text(viewModel.result.selectedBasket.missingItemsExplanation)
                            .font(BrandTypography.body)
                            .foregroundStyle(viewModel.result.selectedBasket.unavailableItems.isEmpty ? BrandPalette.success : BrandPalette.textSecondary)
                    }

                    if !viewModel.result.selectedBasket.unavailableItems.isEmpty {
                        ForEach(viewModel.result.selectedBasket.unavailableItems) { intent in
                            BrandCard {
                                VStack(alignment: .leading, spacing: 10) {
                                    Text("Could not confidently match: \(intent.quantity)x \(intent.userInput)")
                                        .font(BrandTypography.section)
                                        .foregroundStyle(BrandPalette.navy)
                                    Text("Try broadening the wording or adding a category hint (for example: milk, bread, pasta, rice).")
                                        .font(BrandTypography.caption)
                                        .foregroundStyle(BrandPalette.textSecondary)

                                    let alternatives = viewModel.alternatives(for: intent)
                                    if alternatives.isEmpty {
                                        Text("No strong alternatives available in selected supermarkets yet.")
                                            .font(BrandTypography.caption)
                                            .foregroundStyle(BrandPalette.textSecondary)
                                    } else {
                                        VStack(alignment: .leading, spacing: 6) {
                                            Text("Closest alternatives")
                                                .font(BrandTypography.caption.weight(.semibold))
                                                .foregroundStyle(BrandPalette.blue)
                                            ForEach(alternatives) { alternative in
                                                HStack {
                                                    Text("\(alternative.supermarket.name): \(alternative.product.name)")
                                                        .font(BrandTypography.caption)
                                                    Spacer()
                                                    Text(alternative.totalPrice.asGBP())
                                                        .font(BrandTypography.caption.weight(.semibold))
                                                }
                                                .foregroundStyle(BrandPalette.textSecondary)
                                            }
                                        }
                                    }
                                }
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

    private var decisionSummaryCards: some View {
        VStack(alignment: .leading, spacing: 10) {
            if let cheapestSingle = viewModel.result.cheapestSingleStore {
                premiumDecisionCard(
                    title: "Cheapest Single-Store",
                    total: cheapestSingle.total,
                    storesUsed: [cheapestSingle.supermarket.name],
                    savings: viewModel.result.savingsVsMostExpensive,
                    explanation: "Best one-shop checkout with zero switching between supermarkets.",
                    tint: BrandPalette.blue
                )
            }

            premiumDecisionCard(
                title: "Cheapest Mixed Basket",
                total: viewModel.result.mixedBasket.total,
                storesUsed: viewModel.result.mixedBasket.supermarketsUsed,
                savings: viewModel.mixedBasketSavingsVsSingleStore,
                explanation: "Lowest total cost by combining strongest prices across supermarkets.",
                tint: BrandPalette.success
            )

            if let convenience = viewModel.bestConvenienceOption {
                premiumDecisionCard(
                    title: "Best Convenience Option",
                    total: convenience.total,
                    storesUsed: [convenience.supermarket.name],
                    savings: viewModel.convenienceSavingsVsHighest,
                    explanation: "\(convenience.unavailableItems.count) item(s) missing, but this is the simplest near-complete trip.",
                    tint: BrandPalette.navy
                )
            }

            premiumDecisionCard(
                title: "Savings Summary",
                total: viewModel.result.selectedBasket.total,
                storesUsed: viewModel.selectedStoresUsed,
                savings: viewModel.result.savingsVsCheapestSingleStore,
                explanation: viewModel.savingsExplanation,
                tint: BrandPalette.red
            )
        }
    }

    private func section<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(BrandTypography.section)
                .foregroundStyle(BrandPalette.navy)
            content()
        }
    }

    private func premiumDecisionCard(title: String, total: Decimal, storesUsed: [String], savings: Decimal, explanation: String, tint: Color) -> some View {
        BrandCard {
            VStack(alignment: .leading, spacing: 8) {
                Text(title.uppercased())
                    .font(BrandTypography.caption.weight(.semibold))
                    .foregroundStyle(tint)
                Text(total.asGBP())
                    .font(BrandTypography.title)
                    .foregroundStyle(tint)
                Text("Stores used: \(storesUsed.isEmpty ? "None" : storesUsed.joined(separator: ", "))")
                    .font(BrandTypography.caption)
                    .foregroundStyle(BrandPalette.textSecondary)
                Text("Savings: \(savings.asGBP())")
                    .font(BrandTypography.caption.weight(.semibold))
                    .foregroundStyle(BrandPalette.navy)
                Text(explanation)
                    .font(BrandTypography.caption)
                    .foregroundStyle(BrandPalette.textSecondary)
            }
        }
    }

    private func isCheapestSingleStore(_ total: SupermarketBasketTotal) -> Bool {
        viewModel.result.cheapestSingleStore?.supermarket.id == total.supermarket.id
    }
}
