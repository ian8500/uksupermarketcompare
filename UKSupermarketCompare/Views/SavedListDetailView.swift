import SwiftUI

struct SavedListDetailView: View {
    let shoppingList: ShoppingList

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                BrandHeader(title: shoppingList.title, subtitle: "Saved on \(shoppingList.createdAt.formatted(date: .abbreviated, time: .omitted)).")

                ForEach(shoppingList.items) { item in
                    BrandCard {
                        HStack {
                            Text(item.name)
                                .font(BrandTypography.body)
                            Spacer()
                            BrandBadge(text: "x\(item.quantity)", tint: BrandPalette.red)
                        }
                    }
                }
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Saved List")
    }
}
