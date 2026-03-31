import SwiftUI

struct CreateShoppingListView: View {
    @ObservedObject var viewModel: CreateShoppingListViewModel

    var body: some View {
        ScrollView {
            VStack(spacing: 14) {
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

                        HStack {
                            Text("Quantity")
                                .font(BrandTypography.body)
                                .foregroundStyle(BrandPalette.textPrimary)
                            Spacer()
                            Stepper("\(viewModel.quantity)", value: $viewModel.quantity, in: 1...20)
                                .labelsHidden()
                            Text("\(viewModel.quantity)")
                                .font(BrandTypography.section)
                                .foregroundStyle(BrandPalette.blue)
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
                        sectionTitle("Current Basket")

                        if viewModel.items.isEmpty {
                            Text("No items yet. Add at least one item to continue.")
                                .font(BrandTypography.body)
                                .foregroundStyle(BrandPalette.textSecondary)
                        } else {
                            ForEach(Array(viewModel.items.enumerated()), id: \.element.id) { index, item in
                                HStack {
                                    Text(item.name)
                                        .font(BrandTypography.body)
                                    Spacer()
                                    BrandBadge(text: "x\(item.quantity)", tint: BrandPalette.red)
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

    private func sectionTitle(_ text: String) -> some View {
        Text(text)
            .font(BrandTypography.section)
            .foregroundStyle(BrandPalette.navy)
    }
}
