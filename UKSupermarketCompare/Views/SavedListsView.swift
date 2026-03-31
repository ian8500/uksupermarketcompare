import SwiftUI

struct SavedListsView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: SavedListsViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                BrandHeader(title: "Saved lists", subtitle: "Reuse baskets and compare again in seconds.")

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
                        Button {
                            coordinator.openSavedListDetail(list)
                        } label: {
                            BrandCard {
                                HStack {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(list.title)
                                            .font(BrandTypography.section)
                                            .foregroundStyle(BrandPalette.navy)
                                        Text("\(list.items.count) items")
                                            .font(BrandTypography.caption)
                                            .foregroundStyle(BrandPalette.textSecondary)
                                    }
                                    Spacer()
                                    Image(systemName: "chevron.right")
                                        .foregroundStyle(BrandPalette.textSecondary)
                                }
                            }
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding()
        }
        .brandScreenBackground()
        .navigationTitle("Saved Lists")
    }
}
