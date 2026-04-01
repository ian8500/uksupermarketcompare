import SwiftUI

struct BasketComparisonResultsView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: BasketComparisonResultsViewModel
    @State private var didSave = false
    @State private var revealSections = false
    @State private var highlightedStrategyID: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BrandMetrics.spacingLG) {
                BrandHeader(title: "Premium basket decision", subtitle: "Clear outcomes, practical plan, confident checkout.")
                DataSourceBadgeView(status: coordinator.dataSourceStatus)

                heroResultCard
                    .opacity(revealSections ? 1 : 0)
                    .offset(y: revealSections ? 0 : 12)

                section("Decision cards") {
                    decisionSummaryCards
                }

                section("Why this plan") {
                    BrandCard {
                        VStack(alignment: .leading, spacing: 10) {
                            Text(viewModel.selectedStrategyReason)
                                .font(BrandTypography.body)
                                .foregroundStyle(BrandPalette.textPrimary)
                            Text(viewModel.strategyTradeOffSummary)
                                .font(BrandTypography.caption)
                                .foregroundStyle(BrandPalette.textSecondary)
                            Text(viewModel.convenienceVsSavingsSummary)
                                .font(BrandTypography.caption)
                                .foregroundStyle(BrandPalette.textSecondary)
                        }
                    }
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
                            VStack(alignment: .leading, spacing: 10) {
                                Text("Action plan")
                                    .font(BrandTypography.section)
                                    .foregroundStyle(BrandPalette.navy)
                                Text("Grouped by store for quick checkout.")
                                    .font(BrandTypography.caption)
                                    .foregroundStyle(BrandPalette.textSecondary)
                                HStack(spacing: 8) {
                                    BrandChip(text: "\(viewModel.selectedStoresUsed.count) stores", tint: BrandPalette.blue)
                                    BrandChip(text: "Overall \(viewModel.purchasePlanOverallTotal.asGBP())", tint: BrandPalette.success)
                                }
                                Text("Selected strategy: \(viewModel.selectedModeTitle) — \(viewModel.selectedModeSummary)")
                                    .font(BrandTypography.caption)
                                    .foregroundStyle(BrandPalette.textSecondary)
                            }
                        }

                        ForEach(Array(viewModel.purchasePlanByStore.enumerated()), id: \.element.id) { index, group in
                            BrandCard {
                                VStack(alignment: .leading, spacing: 10) {
                                    HStack(alignment: .top) {
                                        VStack(alignment: .leading, spacing: 4) {
                                            Text(group.supermarket.name)
                                                .font(BrandTypography.section)
                                            HStack(spacing: 8) {
                                                BrandBadge(text: "\(group.itemCount) items", tint: BrandPalette.navy)
                                                BrandBadge(text: "Subtotal \(group.subtotal.asGBP())", tint: BrandPalette.blue)
                                            }
                                        }
                                        Spacer()
                                    }

                                    ForEach(group.selections) { selection in
                                        HStack(alignment: .top) {
                                            VStack(alignment: .leading, spacing: 4) {
                                                Text("\(selection.quantity)x \(selection.product.name)")
                                                    .font(BrandTypography.body)
                                                Text("\(selection.intent.userInput) • \(selection.matchQuality.label) match • confidence \(Int((selection.confidence as NSDecimalNumber).doubleValue * 100))%")
                                                    .font(BrandTypography.caption)
                                                    .foregroundStyle(BrandPalette.textSecondary)
                                                Text(viewModel.decisionExplanation(for: selection))
                                                    .font(BrandTypography.caption)
                                                    .foregroundStyle(BrandPalette.textSecondary)
                                            }
                                            Spacer()
                                            Text(selection.totalPrice.asGBP())
                                                .font(BrandTypography.section)
                                                .foregroundStyle(BrandPalette.navy)
                                        }
                                        .padding(8)
                                        .background(BrandPalette.cloud.opacity(0.5))
                                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                                        if selection.id != group.selections.last?.id {
                                            Divider()
                                        }
                                    }
                                }
                            }
                            .opacity(revealSections ? 1 : 0)
                            .offset(y: revealSections ? 0 : 8)
                            .animation(.easeOut(duration: 0.35).delay(0.08 * Double(index + 1)), value: revealSections)
                        }
                    }
                }

                section("Savings story") {
                    BrandCard {
                        Text(viewModel.savingsStory)
                            .font(BrandTypography.body)
                            .foregroundStyle(BrandPalette.textPrimary)
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
                        VStack(alignment: .leading, spacing: 8) {
                            Text(viewModel.missingItemsSummary)
                                .font(BrandTypography.body)
                                .foregroundStyle(viewModel.result.selectedBasket.unavailableItems.isEmpty ? BrandPalette.success : BrandPalette.textSecondary)
                            if !viewModel.result.selectedBasket.unavailableItems.isEmpty {
                                Text(viewModel.result.selectedBasket.missingItemsExplanation)
                                    .font(BrandTypography.caption)
                                    .foregroundStyle(BrandPalette.textSecondary)
                            }
                        }
                    }

                    if !viewModel.result.selectedBasket.unavailableItems.isEmpty {
                        ForEach(viewModel.result.selectedBasket.unavailableItems) { intent in
                            BrandCard {
                                VStack(alignment: .leading, spacing: 10) {
                                    Text("Could not confidently match: \(intent.quantity)x \(intent.userInput)")
                                        .font(BrandTypography.section)
                                        .foregroundStyle(BrandPalette.navy)
                                    Text("Try broader wording or a category hint, for example: milk, bread, pasta, rice.")
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

                VStack(spacing: 10) {
                    Button(didSave ? "Saved to your baskets" : "Save this basket") {
                        viewModel.saveList()
                        HapticFeedbackService.saveBasket()
                        didSave = true
                    }
                    .buttonStyle(BrandPrimaryButtonStyle())
                    .disabled(didSave)

                    Button("Build another basket") {
                        coordinator.path.removeAll()
                    }
                    .buttonStyle(BrandSecondaryButtonStyle())
                }
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Results")
        .onAppear {
            revealSections = true
            HapticFeedbackService.bestOptionSelected()
        }
        .animation(.easeOut(duration: 0.25), value: revealSections)
    }

    private var decisionSummaryCards: some View {
        VStack(alignment: .leading, spacing: 10) {
            ForEach(Array(viewModel.strategyCards.enumerated()), id: \.element.id) { index, card in
                premiumDecisionCard(card: card)
                    .opacity(revealSections ? 1 : 0)
                    .offset(y: revealSections ? 0 : 10)
                    .animation(.easeOut(duration: 0.3).delay(0.06 * Double(index + 1)), value: revealSections)
            }
        }
    }

    private func section<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(BrandTypography.section)
                .foregroundStyle(BrandPalette.navy)
            content()
                .opacity(revealSections ? 1 : 0)
                .offset(y: revealSections ? 0 : 8)
        }
    }

    private func premiumDecisionCard(card: BasketComparisonResultsViewModel.StrategyCard) -> some View {
        let tint = card.tint == "green" ? BrandPalette.success : card.tint == "blue" ? BrandPalette.blue : card.tint == "navy" ? BrandPalette.navy : BrandPalette.red
        let isHighlighted = highlightedStrategyID == card.id || (highlightedStrategyID == nil && card.isSelected)

        return BrandCard {
            VStack(alignment: .leading, spacing: BrandMetrics.spacingSM) {
                HStack {
                    Text(card.title.uppercased())
                    if card.isSelected {
                        Spacer()
                        BrandBadge(text: "Selected", tint: BrandPalette.red)
                    }
                }
                    .font(BrandTypography.caption.weight(.semibold))
                    .foregroundStyle(tint)
                HStack(spacing: BrandMetrics.spacingXS) {
                    if card.title.contains("Cheapest") {
                        BrandBadge(text: "Cheapest", tint: BrandPalette.success)
                    }
                    if card.title.contains("Convenience") {
                        BrandBadge(text: "Fastest", tint: BrandPalette.blue)
                    }
                    if card.storesUsed.count == 1 {
                        BrandBadge(text: "1 store", tint: BrandPalette.navy)
                    }
                }
                Text(card.total.asGBP())
                    .font(BrandTypography.hero)
                    .foregroundStyle(tint)
                Text("Stores used: \(card.storesUsed.isEmpty ? "None" : card.storesUsed.joined(separator: ", "))")
                    .font(BrandTypography.caption)
                    .foregroundStyle(BrandPalette.textSecondary)
                Text(card.savingsHeadline)
                    .font(BrandTypography.caption.weight(.semibold))
                    .foregroundStyle(BrandPalette.navy)
                Text(card.explanation)
                    .font(BrandTypography.caption)
                    .foregroundStyle(BrandPalette.textSecondary)
            }
        }
        .overlay {
            RoundedRectangle(cornerRadius: BrandMetrics.cardRadius, style: .continuous)
                .stroke(isHighlighted ? tint.opacity(0.5) : .clear, lineWidth: 2)
        }
        .scaleEffect(isHighlighted ? 1 : 0.985)
        .onTapGesture {
            highlightedStrategyID = card.id
            HapticFeedbackService.tap()
        }
        .animation(.spring(response: 0.28, dampingFraction: 0.85), value: isHighlighted)
    }

    private func isCheapestSingleStore(_ total: SupermarketBasketTotal) -> Bool {
        viewModel.result.cheapestSingleStore?.supermarket.id == total.supermarket.id
    }
}

private extension BasketComparisonResultsView {
    var heroResultCard: some View {
        VStack(alignment: .leading, spacing: BrandMetrics.spacingSM) {
            Text("Best shop this week")
                .font(BrandTypography.section)
                .foregroundStyle(.white.opacity(0.92))
            AnimatedCurrencyText(value: viewModel.result.selectedBasket.total)
                .font(BrandTypography.display)
                .foregroundStyle(.white)

            Text("Your selected checkout strategy: \(viewModel.selectedModeTitle)")
                .font(BrandTypography.body.weight(.medium))
                .foregroundStyle(.white.opacity(0.94))

            HStack(spacing: 8) {
                BrandChip(text: "Save \(viewModel.result.savingsVsMostExpensive.asGBP()) vs alternative", tint: .white)
                BrandChip(text: "\(viewModel.selectedStoresUsed.count) store(s)", tint: .white)
            }
        }
        .padding(BrandMetrics.spacingLG)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: BrandMetrics.cardRadius, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [BrandPalette.red, BrandPalette.blue],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
        )
        .overlay(
            RoundedRectangle(cornerRadius: BrandMetrics.cardRadius, style: .continuous)
                .stroke(.white.opacity(0.22), lineWidth: 1)
        )
        .shadow(color: BrandPalette.blue.opacity(0.28), radius: 16, y: 9)
    }
}


private struct AnimatedCurrencyText: View {
    let value: Decimal
    @State private var displayedValue: Double = 0

    var body: some View {
        Text(Decimal(displayedValue).asGBP())
            .contentTransition(.numericText(value: displayedValue))
            .opacity(displayedValue == 0 ? 0.5 : 1)
            .onAppear {
                withAnimation(.easeOut(duration: 0.75)) {
                    displayedValue = (value as NSDecimalNumber).doubleValue
                }
            }
    }
}
