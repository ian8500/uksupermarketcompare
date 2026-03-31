import SwiftUI

struct BasketComparisonResultsView: View {
    @ObservedObject var viewModel: BasketComparisonResultsViewModel
    @State private var didSave = false

    var body: some View {
        List {
            Section("Basket") {
                Text(viewModel.result.shoppingList.title)
                    .font(.headline)
                ForEach(viewModel.result.shoppingList.items) { item in
                    HStack {
                        Text(item.name)
                        Spacer()
                        Text("x\(item.quantity)")
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Section("Comparison Results") {
                ForEach(viewModel.result.prices) { line in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(line.supermarketName)
                            if line.id == viewModel.result.bestOption?.id {
                                Text("Best Value")
                                    .font(.caption)
                                    .foregroundStyle(.green)
                            }
                        }
                        Spacer()
                        Text(line.subtotal, format: .currency(code: "GBP"))
                            .fontWeight(.semibold)
                    }
                }
            }

            Section {
                Button(didSave ? "Saved" : "Save List") {
                    viewModel.saveList()
                    didSave = true
                }
                .disabled(didSave)
            }
        }
        .navigationTitle("Basket Comparison Results")
    }
}
