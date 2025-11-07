import SwiftUI

struct SettingsView: View {
    let session: UserSession
    @EnvironmentObject private var appModel: AppModel
    @State private var showSignOutConfirmation = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Account") {
                    LabeledContent("Email", value: session.user.email)
                    if let display = session.user.displayName {
                        LabeledContent("Display Name", value: display)
                    }
                    LabeledContent("Timezone", value: session.user.timezone)
                }

                Section {
                    Button(role: .destructive) {
                        showSignOutConfirmation = true
                    } label: {
                        Text("Sign Out")
                    }
                }
            }
            .navigationTitle("Settings")
            .alert("Sign out?", isPresented: $showSignOutConfirmation) {
                Button("Cancel", role: .cancel) {}
                Button("Sign Out", role: .destructive) {
                    Task { await appModel.signOut() }
                }
            } message: {
                Text("You can sign back in at any time.")
            }
        }
    }
}
