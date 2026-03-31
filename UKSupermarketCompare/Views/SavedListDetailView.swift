import SwiftUI

struct SavedListDetailView: View {
    let shoppingList: ShoppingList

    var body: some View {
        List {
            Section("List Info") {
                Text(shoppingList.title)
                Text(shoppingList.createdAt, style: .date)
                    .foregroundStyle(.secondary)
            }

            Section("Items") {
                ForEach(shoppingList.items) { item in
                    HStack {
                        Text(item.name)
                        Spacer()
                        Text("x\(item.quantity)")
                    }
                }
            }
        }
        .navigationTitle("Saved List")
    }
}
