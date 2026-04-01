import SwiftUI

struct CreateShoppingListView: View {
    @ObservedObject var viewModel: CreateShoppingListViewModel

    var body: some View {
        ScrollView {
            VStack(spacing: 14) {
                BrandHeader(title: "Build your basket", subtitle: "Add groceries quickly with smart suggestions.")

                BrandCard {
                    VStack(alignment: .leading, spacing: 10) {
                        sectionTitle("List Name")
                        TextField("Weekly Shop", text: $viewModel.listTitle)
                            .textInputAutocapitalization(.words)
                            .padding(12)
                            .background(BrandPalette.cloud)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    }
                }

                BrandCard {
                    VStack(alignment: .leading, spacing: 10) {
                        sectionTitle("Add Item")
                        TextField("Item name", text: $viewModel.itemName)
                            .padding(12)
                            .background(BrandPalette.cloud)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

                        if !viewModel.suggestions.isEmpty {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 8) {
                                    ForEach(viewModel.suggestions.prefix(8)) { suggestion in
                                        Button {
                                            viewModel.applySuggestion(suggestion)
                                        } label: {
                                            VStack(alignment: .leading, spacing: 2) {
                                                Text(suggestion.item.displayName)
                                                Text(suggestion.hintText)
                                                    .font(BrandTypography.caption)
                                            }
                                            .foregroundStyle(BrandPalette.navy)
                                            .padding(.horizontal, 10)
                                            .padding(.vertical, 8)
                                            .background(BrandPalette.blue.opacity(0.10))
                                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                                        }
                                        .buttonStyle(.plain)
                                    }
                                }
                            }
                        }

                        HStack {
                            Text("Quantity")
                                .font(BrandTypography.body)
                                .foregroundStyle(BrandPalette.textPrimary)
                            Spacer()
                            quantityStepper
                        }

                        Button("Add Item") {
                            viewModel.addItem()
                        }
                        .buttonStyle(BrandSecondaryButtonStyle())
                        .disabled(!viewModel.canAddItem)
                    }
                }



                BrandCard {
                    VStack(alignment: .leading, spacing: 10) {
                        sectionTitle("Weekly essentials")
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(viewModel.weeklyEssentials, id: \.self) { item in
                                    Button(item) { viewModel.quickAddEssential(item) }
                                        .buttonStyle(BrandSecondaryButtonStyle())
                                }
                            }
                        }
                    }
                }

                if !viewModel.recentItems.isEmpty {
                    BrandCard {
                        VStack(alignment: .leading, spacing: 10) {
                            sectionTitle("Recent items")
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 8) {
                                    ForEach(viewModel.recentItems.prefix(10), id: \.self) { item in
                                        Button(item) { viewModel.addRecentItem(item) }
                                            .buttonStyle(.bordered)
                                            .tint(BrandPalette.blue)
                                    }
                                }
                            }
                        }
                    }
                }

                BrandCard {
                    VStack(alignment: .leading, spacing: 10) {
                        sectionTitle("Current Basket")

                        if viewModel.items.isEmpty {
                            VStack(spacing: 6) {
                                Image(systemName: "basket")
                                    .font(.title2)
                                    .foregroundStyle(BrandPalette.blue)
                                Text("No items yet")
                                    .font(BrandTypography.section)
                                    .foregroundStyle(BrandPalette.navy)
                                Text("Start with suggestions above or type your first grocery item.")
                                    .font(BrandTypography.caption)
                                    .foregroundStyle(BrandPalette.textSecondary)
                                    .multilineTextAlignment(.center)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 8)
                        } else {
                            ForEach(Array(viewModel.items.enumerated()), id: \.element.id) { index, item in
                                HStack(spacing: 8) {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(item.name)
                                            .font(BrandTypography.body)
                                        BrandChip(text: "Qty \(item.quantity)", tint: BrandPalette.red)
                                    }
                                    Spacer()
                                    itemQuantityStepper(for: item.id)
                                    Button {
                                        viewModel.deleteItem(at: IndexSet(integer: index))
                                    } label: {
                                        Image(systemName: "trash")
                                            .foregroundStyle(BrandPalette.red)
                                    }
                                }
                                .padding(.vertical, 2)
                            }
                        }
                    }
                }

                Button("Continue to Supermarket Selection") {
                    viewModel.continueToSupermarketSelection()
                }
                .buttonStyle(BrandPrimaryButtonStyle())
                .disabled(!viewModel.canContinue)
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Create Shopping List")
    }

    private var quantityStepper: some View {
        HStack(spacing: 10) {
            stepperButton(systemImage: "minus", disabled: viewModel.quantity <= 1) {
                viewModel.quantity = max(1, viewModel.quantity - 1)
            }

            Text("\(viewModel.quantity)")
                .font(BrandTypography.section)
                .foregroundStyle(BrandPalette.blue)
                .frame(minWidth: 26)

            stepperButton(systemImage: "plus") {
                viewModel.quantity = min(99, viewModel.quantity + 1)
            }
        }
        .padding(8)
        .background(BrandPalette.cloud)
        .clipShape(Capsule())
    }

    private func itemQuantityStepper(for itemID: UUID) -> some View {
        HStack(spacing: 8) {
            stepperButton(systemImage: "minus") {
                viewModel.updateQuantity(for: itemID, delta: -1)
            }
            stepperButton(systemImage: "plus") {
                viewModel.updateQuantity(for: itemID, delta: 1)
            }
        }
    }

    private func stepperButton(systemImage: String, disabled: Bool = false, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: systemImage)
                .font(.caption.weight(.bold))
                .frame(width: 26, height: 26)
                .background(BrandPalette.blue.opacity(disabled ? 0.1 : 0.14))
                .foregroundStyle(disabled ? BrandPalette.textSecondary : BrandPalette.blue)
                .clipShape(Circle())
        }
        .buttonStyle(.plain)
        .disabled(disabled)
    }

    private func sectionTitle(_ text: String) -> some View {
        Text(text)
            .font(BrandTypography.section)
            .foregroundStyle(BrandPalette.navy)
    }
}
