import SwiftUI

struct MainTabView: View {
    let session: UserSession

    var body: some View {
        TabView {
            AgendaView()
                .tabItem {
                    Label("Today", systemImage: "checklist")
                }

            PlannerDashboardView()
                .tabItem {
                    Label("Planner", systemImage: "calendar")
                }

            MemoryReviewView()
                .tabItem {
                    Label("Memory", systemImage: "brain.head.profile")
                }

            SettingsView(session: session)
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
        }
    }
}
