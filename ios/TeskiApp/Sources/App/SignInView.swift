import SwiftUI

struct SignInView: View {
    @EnvironmentObject private var appModel: AppModel
    @State private var email: String = ""
    @State private var password: String = ""
    @State private var isSubmitting = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Account") {
                    TextField("Email", text: $email)
                        .keyboardType(.emailAddress)
                        .textContentType(.username)
                        .autocapitalization(.none)
                    SecureField("Password", text: $password)
                        .textContentType(.password)
                }

                Section {
                    Button {
                        Task { await submit() }
                    } label: {
                        if isSubmitting {
                            ProgressView()
                        } else {
                            Text("Sign In")
                        }
                    }
                    .disabled(isSubmitting || email.isEmpty || password.isEmpty)
                }
            }
            .navigationTitle("Welcome to Teski")
        }
    }

    private func submit() async {
        guard !isSubmitting else { return }
        isSubmitting = true
        defer { isSubmitting = false }
        await appModel.signIn(email: email, password: password)
    }
}
