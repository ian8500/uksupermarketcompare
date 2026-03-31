import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var coordinator: AppCoordinatorViewModel
    @ObservedObject var viewModel: HomeViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text(viewModel.title)
                .font(.largeTitle.bold())
            Text(viewModel.subtitle)
                .foregroundStyle(.secondary)

            Spacer()

            Button("Create Shopping List") {
                coordinator.openCreateList()
            }
            .buttonStyle(.borderedProminent)

            Button("View Saved Lists") {
                coordinator.openSavedLists()
            }
            .buttonStyle(.bordered)

            Spacer()
        }
        .padding()
        .navigationTitle("Welcome")
    }
}
