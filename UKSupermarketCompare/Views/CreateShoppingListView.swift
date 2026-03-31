import SwiftUI

struct CreateShoppingListView: View {
    @ObservedObject var viewModel: CreateShoppingListViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.lg) {
                AppSectionHeader(title: "Create shopping list", subtitle: "Search your groceries and build a comparison-ready basket.")

                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text("List name")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                    TextField("Weekly Shop", text: $viewModel.listTitle)
                        .textFieldStyle(.roundedBorder)
                }
                .appCardStyle()

                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text("Add item")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)

                    TextField("Try milk, pasta, tomatoes...", text: $viewModel.itemName)
                        .textFieldStyle(.roundedBorder)

                    Stepper("Quantity: \(viewModel.quantity)", value: $viewModel.quantity, in: 1...20)

                    Button("Add to list") { viewModel.addItem() }
                        .buttonStyle(AppPrimaryButtonStyle())
                        .disabled(!viewModel.canAddItem)

                    if !viewModel.suggestions.isEmpty {
                        VStack(alignment: .leading, spacing: AppSpacing.xs) {
                            Text("Suggestions")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.textSecondary)

                            ForEach(viewModel.suggestions) { suggestion in
                                Button {
                                    viewModel.quickAddSuggestion(suggestion)
                                } label: {
                                    HStack {
                                        VStack(alignment: .leading, spacing: 2) {
                                            Text(suggestion.item.displayName)
                                                .foregroundStyle(AppColors.textPrimary)
                                            Text(suggestion.hintText)
                                                .font(.caption)
                                                .foregroundStyle(AppColors.textSecondary)
                                        }
                                        Spacer()
                                        Image(systemName: "plus.circle.fill")
                                            .foregroundStyle(AppColors.brandRed)
                                    }
                                }
                                .buttonStyle(.plain)
                                Divider()
                            }
                        }
                    }
                }
                .appCardStyle()

                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text("Your basket")
                        .font(AppTypography.sectionTitle)

                    if viewModel.items.isEmpty {
                        AppEmptyState(icon: "list.bullet.rectangle", title: "No items yet", subtitle: "Start typing to get smart grocery suggestions.")
                    } else {
                        ForEach(viewModel.items) { item in
                            HStack(spacing: AppSpacing.md) {
                                VStack(alignment: .leading) {
                                    Text(item.name)
                                        .font(.headline)
                                    Text("Quantity: \(item.quantity)")
                                        .font(.caption)
                                        .foregroundStyle(AppColors.textSecondary)
                                }
                                Spacer()
                                HStack {
                                    Button { viewModel.updateQuantity(for: item.id, delta: -1) } label: { Image(systemName: "minus.circle") }
                                    Button { viewModel.updateQuantity(for: item.id, delta: 1) } label: { Image(systemName: "plus.circle") }
                                    Button {
                                        if let index = viewModel.items.firstIndex(where: { $0.id == item.id }) {
                                            viewModel.deleteItem(at: IndexSet(integer: index))
                                        }
                                    } label: { Image(systemName: "trash") }
                                }
                                .buttonStyle(.plain)
                                .foregroundStyle(AppColors.brandBlue)
                            }
                            .padding(.vertical, 6)
                        }
                    }
                }
                .appCardStyle()

                Button("Continue to supermarket selection") {
                    viewModel.continueToSupermarketSelection()
                }
                .buttonStyle(AppPrimaryButtonStyle())
                .disabled(!viewModel.canContinue)
            }
            .padding(AppSpacing.md)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Shopping List")
    }
}
