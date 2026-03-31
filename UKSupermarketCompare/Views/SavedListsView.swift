import SwiftUI

struct SavedListsView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: SavedListsViewModel

    var body: some View {
        List {
            if viewModel.savedLists.isEmpty {
                Text("No saved lists yet. Save a comparison result to find it here.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(viewModel.savedLists) { list in
                    Button {
                        coordinator.openSavedListDetail(list)
                    } label: {
                        VStack(alignment: .leading) {
                            Text(list.title)
                            Text("\(list.items.count) items")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .onDelete(perform: viewModel.delete)
            }
        }
        .navigationTitle("Saved Lists")
    }
}
