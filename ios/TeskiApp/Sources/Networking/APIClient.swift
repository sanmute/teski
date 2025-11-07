import Foundation

protocol APIClientProtocol {
    func get<T: Decodable>(path: String, queryItems: [URLQueryItem]) async throws -> T
    func post<Body: Encodable, Response: Decodable>(path: String, body: Body, headers: [String: String]) async throws -> Response
}

actor APIClient: APIClientProtocol {
    nonisolated static let shared = APIClient()

    private let baseURL: URL
    private let urlSession: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder
    private var authTokenProvider: () async -> String? = { nil }

    init(baseURL: URL = URL(string: "https://api.teski.app")!, urlSession: URLSession = .shared) {
        self.baseURL = baseURL
        self.urlSession = urlSession
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        self.decoder = decoder
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        self.encoder = encoder
    }

    func configureAuthTokenProvider(_ provider: @escaping () async -> String?) {
        authTokenProvider = provider
    }

    func get<T: Decodable>(path: String, queryItems: [URLQueryItem] = []) async throws -> T {
        var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        components.queryItems = queryItems.isEmpty ? nil : queryItems
        var request = URLRequest(url: components.url!)
        request.httpMethod = "GET"
        if let token = await authTokenProvider() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return try await perform(request: request)
    }

    func post<Body: Encodable, Response: Decodable>(path: String, body: Body, headers: [String: String] = [:]) async throws -> Response {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        headers.forEach { request.setValue($0.value, forHTTPHeaderField: $0.key) }
        if request.value(forHTTPHeaderField: "Content-Type") == nil {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        if let token = await authTokenProvider() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = try encoder.encode(body)
        return try await perform(request: request)
    }

    private func perform<T: Decodable>(request: URLRequest) async throws -> T {
        let (data, response) = try await urlSession.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }
        guard 200..<300 ~= http.statusCode else {
            throw APIError.server(http.statusCode, data)
        }
        return try decoder.decode(T.self, from: data)
    }
}

enum APIError: Error {
    case invalidResponse
    case server(Int, Data)
}
