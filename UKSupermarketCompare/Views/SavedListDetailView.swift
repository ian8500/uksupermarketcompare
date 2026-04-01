import SwiftUI

struct SavedListDetailView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @State private var shoppingList: ShoppingList
    @State private var editedTitle: String

    init(shoppingList: ShoppingList) {
        _shoppingList = State(initialValue: shoppingList)
        _editedTitle = State(initialValue: shoppingList.title)
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                BrandHeader(title: shoppingList.title, subtitle: "Saved on \(shoppingList.createdAt.formatted(date: .abbreviated, time: .omitted)).")

                BrandCard {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Edit basket title")
                            .font(BrandTypography.section)
                        TextField("List title", text: $editedTitle)
                            .textInputAutocapitalization(.words)
                            .padding(10)
                            .background(BrandPalette.cloud)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                        Button("Save edits") {
                            shoppingList.title = editedTitle.trimmingCharacters(in: .whitespacesAndNewlines)
                            coordinator.store.update(list: shoppingList)
                        }
                        .buttonStyle(BrandSecondaryButtonStyle())
                    }
                }

                HStack(spacing: 8) {
                    Button("Rerun basket") {
                        coordinator.store.markCompared(listID: shoppingList.id)
                        coordinator.openSelection(for: shoppingList)
                    }
                    .buttonStyle(BrandPrimaryButtonStyle())

                    Button("Duplicate") {
                        coordinator.store.duplicate(listID: shoppingList.id)
                    }
                    .buttonStyle(BrandSecondaryButtonStyle())
                }

                ForEach(Array(shoppingList.items.enumerated()), id: \.element.id) { index, item in
                    BrandCard {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(item.name)
                                    .font(BrandTypography.body)
                                Stepper("Qty \(item.quantity)", value: bindingForQuantity(at: index), in: 1...99)
                                    .labelsHidden()
                            }
                            Spacer()
                            BrandBadge(text: "x\(item.quantity)", tint: BrandPalette.red)
                            Button {
                                shoppingList.items.remove(at: index)
                                coordinator.store.update(list: shoppingList)
                            } label: {
                                Image(systemName: "trash")
                                    .foregroundStyle(BrandPalette.red)
                            }
                        }
                    }
                }
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Saved List")
    }

    private func bindingForQuantity(at index: Int) -> Binding<Int> {
        Binding(
            get: { shoppingList.items[index].quantity },
            set: { newValue in
                shoppingList.items[index].quantity = newValue
                coordinator.store.update(list: shoppingList)
            }
        )
    }
}
