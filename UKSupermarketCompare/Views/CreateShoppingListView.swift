import SwiftUI

struct CreateShoppingListView: View {
    @ObservedObject var viewModel: CreateShoppingListViewModel

    var body: some View {
        Form {
            Section("List Name") {
                TextField("Weekly Shop", text: $viewModel.listTitle)
            }

            Section("Add Item") {
                TextField("Item name", text: $viewModel.itemName)
                Stepper("Quantity: \(viewModel.quantity)", value: $viewModel.quantity, in: 1...20)
                Button("Add Item") {
                    viewModel.addItem()
                }
                .disabled(!viewModel.canAddItem)
            }

            Section("Current Basket") {
                if viewModel.items.isEmpty {
                    Text("No items yet. Add at least one item to continue.")
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(viewModel.items) { item in
                        HStack {
                            Text(item.name)
                            Spacer()
                            Text("x\(item.quantity)")
                                .foregroundStyle(.secondary)
                        }
                    }
                    .onDelete(perform: viewModel.deleteItem)
                }
            }

            Section {
                Button("Continue to Supermarket Selection") {
                    viewModel.continueToSupermarketSelection()
                }
                .disabled(!viewModel.canContinue)
            }
        }
        .navigationTitle("Create Shopping List")
    }
}
