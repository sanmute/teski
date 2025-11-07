import SwiftUI

struct MemoryReviewView: View {
    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                Image(systemName: "brain")
                    .font(.system(size: 48))
                    .foregroundColor(.accentColor)
                Text("Memory reviews")
                    .font(.headline)
                Text("Practice sessions will live here. We'll pull in due cards and track streaks.")
                    .font(.subheadline)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.secondary)
            }
            .padding()
            .navigationTitle("Memory")
        }
    }
}
