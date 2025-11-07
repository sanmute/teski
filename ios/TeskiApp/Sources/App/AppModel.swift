import Foundation
import Combine

@MainActor
final class AppModel: ObservableObject {
    enum AppState {
        case loading
        case unauthenticated
        case authenticated(UserSession)
    }

    @Published private(set) var state: AppState = .loading

    private let authService: AuthServiceProtocol

    init(authService: AuthServiceProtocol = AuthService()) {
        self.authService = authService
        Task {
            await bootstrap()
        }
    }

    func bootstrap() async {
        do {
            if let session = try await authService.restoreSession() {
                state = .authenticated(session)
            } else {
                state = .unauthenticated
            }
        } catch {
            state = .unauthenticated
        }
    }

    func signIn(email: String, password: String) async {
        do {
            let session = try await authService.signIn(email: email, password: password)
            state = .authenticated(session)
        } catch {
            // TODO: handle error messaging
        }
    }

    func signOut() async {
        await authService.signOut()
        state = .unauthenticated
    }
}
