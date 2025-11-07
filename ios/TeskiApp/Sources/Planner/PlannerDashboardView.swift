import SwiftUI

struct PlannerDashboardView: View {
    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                Image(systemName: "calendar.badge.clock")
                    .font(.system(size: 48))
                    .foregroundColor(.accentColor)
                Text("Planner coming soon")
                    .font(.headline)
                Text("You'll be able to review exams, topics, and regenerate plans here.")
                    .font(.subheadline)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.secondary)
            }
            .padding()
            .navigationTitle("Planner")
        }
    }
}
