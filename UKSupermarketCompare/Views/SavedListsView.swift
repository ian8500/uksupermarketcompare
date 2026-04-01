import SwiftUI

struct SavedListsView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: SavedListsViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                BrandHeader(title: "Saved lists", subtitle: "Reuse baskets and compare again in seconds.")
                if let lastBasket = coordinator.store.lastBasket {
                    BrandCard {
                        VStack(alignment: .leading, spacing: 10) {
                            Text("Continue your weekly loop")
                                .font(BrandTypography.section)
                                .foregroundStyle(BrandPalette.navy)
                            Text("Last basket: \(lastBasket.title)")
                                .font(BrandTypography.body)
                            Button("Rerun last basket now") {
                                coordinator.openSelection(for: lastBasket)
                            }
                            .buttonStyle(BrandPrimaryButtonStyle())
                        }
                    }
                }

                if viewModel.savedLists.isEmpty {
                    BrandCard {
                        VStack(spacing: 8) {
                            Image(systemName: "tray")
                                .font(.title2)
                                .foregroundStyle(BrandPalette.blue)
                            Text("No saved lists yet")
                                .font(BrandTypography.section)
                            Text("Save a comparison result and it will appear here.")
                                .font(BrandTypography.caption)
                                .foregroundStyle(BrandPalette.textSecondary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                    }
                } else {
                    ForEach(viewModel.savedLists) { list in
                        BrandCard {
                            VStack(alignment: .leading, spacing: 10) {
                                HStack {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(list.title)
                                            .font(BrandTypography.section)
                                            .foregroundStyle(BrandPalette.navy)
                                        Text("\(list.items.count) items")
                                            .font(BrandTypography.caption)
                                            .foregroundStyle(BrandPalette.textSecondary)
                                        Text(lastComparedLabel(for: list))
                                            .font(BrandTypography.caption)
                                            .foregroundStyle(BrandPalette.textSecondary)
                                    }
                                    Spacer()
                                    Button {
                                        coordinator.openSavedListDetail(list)
                                    } label: {
                                        Image(systemName: "slider.horizontal.3")
                                    }
                                    .buttonStyle(.bordered)
                                }

                                HStack(spacing: 8) {
                                    Button("Rerun") {
                                        viewModel.rerun(list)
                                        coordinator.openSelection(for: list)
                                    }
                                    .buttonStyle(BrandPrimaryButtonStyle())

                                    Button("Duplicate") {
                                        viewModel.duplicate(list)
                                    }
                                    .buttonStyle(BrandSecondaryButtonStyle())
                                }
                            }
                        }
                    }
                }
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Saved Lists")
    }

    private func lastComparedLabel(for list: ShoppingList) -> String {
        guard let lastComparedAt = list.lastComparedAt else { return "Not compared yet" }
        return "Last compared \(lastComparedAt.formatted(date: .abbreviated, time: .shortened))"
    }
}
