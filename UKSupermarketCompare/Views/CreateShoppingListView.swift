import SwiftUI

struct CreateShoppingListView: View {
    @ObservedObject var viewModel: CreateShoppingListViewModel
    @FocusState private var focusedField: Field?

    private enum Field {
        case itemName
    }

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
                        HStack(spacing: 8) {
                            Image(systemName: "magnifyingglass")
                                .foregroundStyle(BrandPalette.blue)
                            TextField("Search groceries, e.g. 2 milk", text: $viewModel.itemName)
                                .focused($focusedField, equals: .itemName)
                                .submitLabel(.done)
                                .onSubmit { viewModel.addItem() }
                            if !viewModel.itemName.isEmpty {
                                Button {
                                    viewModel.itemName = ""
                                    focusedField = .itemName
                                } label: {
                                    Image(systemName: "xmark.circle.fill")
                                        .foregroundStyle(BrandPalette.textSecondary)
                                }
                            }
                        }
                        .padding(12)
                        .background(BrandPalette.cloud)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12, style: .continuous)
                                .stroke(BrandPalette.blue.opacity(0.2), lineWidth: 1)
                        )
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

                        if !viewModel.suggestions.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                HStack {
                                    Text("Suggestions")
                                        .font(BrandTypography.caption.weight(.semibold))
                                        .foregroundStyle(BrandPalette.textSecondary)
                                    Spacer()
                                    Text(viewModel.suggestionSource == .backend ? "LIVE" : "OFFLINE")
                                        .font(BrandTypography.caption.weight(.semibold))
                                        .foregroundStyle(viewModel.suggestionSource == .backend ? BrandPalette.success : BrandPalette.textSecondary)
                                }
                                ForEach(viewModel.suggestions.prefix(6)) { suggestion in
                                    Button {
                                        viewModel.addSuggestion(suggestion)
                                        focusedField = .itemName
                                    } label: {
                                        HStack {
                                            VStack(alignment: .leading, spacing: 2) {
                                                Text(suggestion.primaryText)
                                                Text(suggestion.hintText)
                                                    .font(BrandTypography.caption)
                                                    .foregroundStyle(BrandPalette.textSecondary)
                                            }
                                            Spacer()
                                            Image(systemName: "plus.circle.fill")
                                                .foregroundStyle(BrandPalette.blue)
                                        }
                                        .padding(10)
                                        .background(BrandPalette.blue.opacity(0.08))
                                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                                    }
                                    .buttonStyle(.plain)
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

                        Button(viewModel.selectedEditItemID == nil ? "Add Item" : "Update Item") {
                            viewModel.applyEditIfNeeded()
                            focusedField = .itemName
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

                        Text("Quick bundles")
                            .font(BrandTypography.caption.weight(.semibold))
                            .foregroundStyle(BrandPalette.textSecondary)
                        ForEach(viewModel.quickStapleBundles, id: \.self) { bundle in
                            Button("Add \(bundle.joined(separator: " + "))") {
                                viewModel.quickAddBundle(bundle)
                            }
                            .buttonStyle(BrandSecondaryButtonStyle())
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
                                        Button(item) {
                                            viewModel.addRecentItem(item)
                                            focusedField = .itemName
                                        }
                                            .buttonStyle(.bordered)
                                            .tint(BrandPalette.blue)
                                    }
                                }
                            }
                        }
                    }
                }

                if !viewModel.favoriteItems.isEmpty {
                    BrandCard {
                        VStack(alignment: .leading, spacing: 10) {
                            sectionTitle("Favorites")
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 8) {
                                    ForEach(viewModel.favoriteItems.prefix(10), id: \.self) { item in
                                        Button {
                                            viewModel.addRecentItem(item)
                                        } label: {
                                            Label(item, systemImage: "star.fill")
                                        }
                                        .buttonStyle(.borderedProminent)
                                        .tint(BrandPalette.red)
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
                                        HStack(spacing: 4) {
                                            Button {
                                                viewModel.toggleFavorite(for: item.name)
                                            } label: {
                                                Image(systemName: viewModel.isFavorite(item.name) ? "star.fill" : "star")
                                                    .foregroundStyle(BrandPalette.red)
                                            }
                                            .buttonStyle(.plain)
                                            Button("Edit") {
                                                viewModel.startEditing(item)
                                                focusedField = .itemName
                                            }
                                            .font(BrandTypography.caption)
                                            .buttonStyle(.plain)
                                            .foregroundStyle(BrandPalette.blue)
                                        }
                                        Text("Quantity")
                                            .font(BrandTypography.caption)
                                            .foregroundStyle(BrandPalette.textSecondary)
                                    }
                                    Spacer()
                                    itemQuantityStepper(for: item.id, quantity: item.quantity)
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

    private func itemQuantityStepper(for itemID: UUID, quantity: Int) -> some View {
        HStack(spacing: 8) {
            stepperButton(systemImage: "minus") {
                viewModel.updateQuantity(for: itemID, delta: -1)
            }
            TextField(
                "Qty",
                value: Binding(
                    get: { quantity },
                    set: { viewModel.setQuantity(for: itemID, to: $0) }
                ),
                format: .number
            )
            .keyboardType(.numberPad)
            .multilineTextAlignment(.center)
            .frame(width: 44)
            .padding(.vertical, 4)
            .background(BrandPalette.cloud)
            .clipShape(RoundedRectangle(cornerRadius: 8))
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
