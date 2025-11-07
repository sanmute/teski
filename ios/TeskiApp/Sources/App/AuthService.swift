import Foundation

protocol AuthServiceProtocol {
    func restoreSession() async throws -> UserSession?
    func signIn(email: String, password: String) async throws -> UserSession
    func signOut() async
}

struct UserSession: Codable, Identifiable {
    let id: UUID
    let token: String
    let refreshToken: String
    let user: UserProfile
}

struct UserProfile: Codable {
    let id: UUID
    let displayName: String?
    let email: String
    let timezone: String
}

final class AuthService: AuthServiceProtocol {
    private enum StorageKeys {
        static let session = "teski.session"
    }

    private let api: APIClientProtocol
    private let storage: SessionStorage

    init(api: APIClientProtocol = APIClient.shared, storage: SessionStorage = KeychainSessionStorage()) {
        self.api = api
        self.storage = storage
        APIClient.shared.configureAuthTokenProvider { [weak storage] in
            await storage?.loadSession()?.token
        }
    }

    func restoreSession() async throws -> UserSession? {
        if let session = await storage.loadSession() {
            return session
        }
        return nil
    }

    func signIn(email: String, password: String) async throws -> UserSession {
        struct Request: Encodable { let email: String; let password: String }
        let response: SignInResponse = try await api.post(path: "/auth/sign-in", body: Request(email: email, password: password))
        let session = response.toSession()
        await storage.saveSession(session)
        return session
    }

    func signOut() async {
        await storage.clearSession()
    }
}

private struct SignInResponse: Decodable {
    let session_id: UUID
    let access_token: String
    let refresh_token: String
    let user: UserDTO

    func toSession() -> UserSession {
        UserSession(id: session_id, token: access_token, refreshToken: refresh_token, user: user.toModel())
    }
}

private struct UserDTO: Decodable {
    let id: UUID
    let display_name: String?
    let email: String
    let timezone: String

    func toModel() -> UserProfile {
        UserProfile(id: id, displayName: display_name, email: email, timezone: timezone)
    }
}

protocol SessionStorage: AnyObject {
    func loadSession() async -> UserSession?
    func saveSession(_ session: UserSession) async
    func clearSession() async
}

final class KeychainSessionStorage: SessionStorage {
    func loadSession() async -> UserSession? { nil }
    func saveSession(_ session: UserSession) async {}
    func clearSession() async {}
}
