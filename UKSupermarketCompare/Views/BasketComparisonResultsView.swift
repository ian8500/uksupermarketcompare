import SwiftUI

struct BasketComparisonResultsView: View {
    @ObservedObject var viewModel: BasketComparisonResultsViewModel
    @State private var didSave = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.md) {
                HStack {
                    AppWordmark()
                    Spacer()
                    AppBadge(text: "Results", tint: AppColors.brandBlue)
                }

                resultHeader
                savingsCards
                rankings
                purchasePlan

                Button(didSave ? "Saved" : "Save list") {
                    viewModel.saveList()
                    didSave = true
                }
                .buttonStyle(AppPrimaryButtonStyle())
                .disabled(didSave)
            }
            .padding(AppSpacing.md)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Best Basket")
    }

    private var resultHeader: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Comparison complete")
                .font(AppTypography.title)
            Text("\(viewModel.result.comparisonMode.title) across \(viewModel.result.supermarketTotals.count) supermarkets")
                .foregroundStyle(AppColors.textSecondary)
            Text(viewModel.result.selectedBasket.total, format: .currency(code: "GBP"))
                .font(.system(size: 30, weight: .bold, design: .rounded))
                .foregroundStyle(AppColors.brandRed)
        }
        .appCardStyle()
    }

    private var savingsCards: some View {
        VStack(spacing: AppSpacing.sm) {
            summaryRow(title: "Cheapest mixed basket", amount: viewModel.result.mixedBasket.total, tint: AppColors.brandBlue)
            if let cheapestSingle = viewModel.result.cheapestSingleStore {
                summaryRow(title: "Cheapest single-store (\(cheapestSingle.supermarket.name))", amount: cheapestSingle.total, tint: AppColors.success)
            }
            summaryRow(title: "Savings vs most expensive", amount: viewModel.result.savingsVsMostExpensive, tint: AppColors.brandRed)
        }
    }

    private var rankings: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            AppSectionHeader(title: "Supermarket ranking", subtitle: "Quickly scan totals and missing items.")
            ForEach(Array(viewModel.result.supermarketTotals.enumerated()), id: \.element.id) { index, total in
                HStack {
                    VStack(alignment: .leading) {
                        Text("#\(index + 1) \(total.supermarket.name)")
                            .font(.headline)
                        Text(total.unavailableItems.isEmpty ? "All items available" : "Missing \(total.unavailableItems.count) item(s)")
                            .font(.caption)
                            .foregroundStyle(AppColors.textSecondary)
                    }
                    Spacer()
                    Text(total.total, format: .currency(code: "GBP"))
                        .font(.headline)
                }
                .appCardStyle()
            }
        }
    }

    private var purchasePlan: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            AppSectionHeader(title: "Item-by-item plan", subtitle: "Use this to buy each item from the best-value store.")
            ForEach(viewModel.result.selectedBasket.selections) { selection in
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("\(selection.quantity)x \(selection.intent.userInput)")
                            .font(.headline)
                        Spacer()
                        Text(selection.totalPrice, format: .currency(code: "GBP"))
                            .font(.headline)
                    }
                    Text(selection.supermarket.name + " • " + selection.product.name)
                        .font(.caption)
                        .foregroundStyle(AppColors.textSecondary)
                    HStack {
                        AppBadge(text: selection.matchQuality.label, tint: AppColors.brandBlue)
                        if selection.product.isOwnBrand { AppBadge(text: "Own-brand", tint: AppColors.success) }
                    }
                }
                .appCardStyle()
            }
        }
    }

    private func summaryRow(title: String, amount: Decimal, tint: Color) -> some View {
        HStack {
            Text(title)
            Spacer()
            Text(amount, format: .currency(code: "GBP"))
                .font(.headline)
                .foregroundStyle(tint)
        }
        .appCardStyle()
    }
}
