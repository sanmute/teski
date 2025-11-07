import SwiftUI

struct AgendaView: View {
    @StateObject private var viewModel = AgendaViewModel()

    var body: some View {
        NavigationStack {
            List {
                if viewModel.reviews.isEmpty && viewModel.blocks.isEmpty {
                    Section {
                        VStack(spacing: 12) {
                            Image(systemName: "sparkles")
                                .font(.system(size: 36))
                                .foregroundColor(.accentColor)
                            Text("All clear for today")
                                .font(.headline)
                            Text("You're caught up. We'll notify you when new reviews or blocks appear.")
                                .font(.subheadline)
                                .multilineTextAlignment(.center)
                                .foregroundColor(.secondary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 24)
                    }
                } else {
                    if !viewModel.reviews.isEmpty {
                        Section("Due Reviews") {
                            ForEach(viewModel.reviews) { item in
                                ReviewRow(item: item)
                            }
                        }
                    }
                    if !viewModel.blocks.isEmpty {
                        Section("Study Blocks") {
                            ForEach(viewModel.blocks) { block in
                                BlockRow(block: block)
                            }
                        }
                    }
                }
            }
            .task { await viewModel.loadAgenda() }
            .refreshable { await viewModel.loadAgenda(force: true) }
            .navigationTitle("Today")
        }
    }
}

private struct ReviewRow: View {
    let item: AgendaReview

    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(item.concept)
                    .font(.headline)
                Text("Due \(item.dueAt, style: .time)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            Spacer()
            Image(systemName: "chevron.right")
                .font(.footnote)
                .foregroundColor(.secondary)
        }
    }
}

private struct BlockRow: View {
    let block: AgendaBlock

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(block.topic)
                    .font(.headline)
                Spacer()
                Text("\(block.minutes) min")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            Text(block.kind.localizedTitle)
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
}
