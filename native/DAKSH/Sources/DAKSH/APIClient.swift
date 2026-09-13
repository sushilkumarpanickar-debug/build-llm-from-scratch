import Foundation

enum APIClientError: LocalizedError, Equatable {
    case invalidBaseURL
    case insecureURL
    case invalidResponse
    case server(status: Int, message: String)

    var errorDescription: String? {
        switch self {
        case .invalidBaseURL:
            "Enter a valid Tailnet HTTPS URL in Settings."
        case .insecureURL:
            "DAKSH only connects to HTTPS endpoints."
        case .invalidResponse:
            "The DAKSH server returned an unreadable response."
        case let .server(status, message):
            "DAKSH server error (\(status)): \(message)"
        }
    }
}

struct APIClient: Sendable {
    let baseURL: URL
    private let session: URLSession

    init(baseURLString: String, session: URLSession = .shared) throws {
        let trimmed = baseURLString.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: trimmed), let host = url.host else {
            throw APIClientError.invalidBaseURL
        }
        let scheme = url.scheme?.lowercased()
        let localHosts = ["localhost", "127.0.0.1", "::1"]
        guard scheme == "https" || (scheme == "http" && localHosts.contains(host.lowercased())) else {
            throw APIClientError.insecureURL
        }
        guard !host.isEmpty else {
            throw APIClientError.invalidBaseURL
        }

        self.baseURL = url
        self.session = session
    }

    func loadHistory(limit: Int = 50) async throws -> [HistoryInteraction] {
        var components = URLComponents(
            url: endpoint(path: "api/daksh/history"),
            resolvingAgainstBaseURL: false
        )!
        components.queryItems = [URLQueryItem(name: "limit", value: String(limit))]
        let response: InteractionHistoryResponse = try await perform(
            URLRequest(url: components.url!)
        )
        return response.history
    }

    func send(input: String) async throws -> InteractionResponse {
        var request = URLRequest(url: endpoint(path: "api/daksh/interact"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.httpBody = try JSONEncoder().encode(InteractionRequest(input: input))
        return try await perform(request)
    }

    private func endpoint(path: String) -> URL {
        baseURL.appending(path: path)
    }

    private func perform<Response: Decodable>(_ request: URLRequest) async throws -> Response {
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.invalidResponse
        }
        guard (200...299).contains(httpResponse.statusCode) else {
            let message = (try? JSONDecoder().decode(ServerError.self, from: data).error)
                ?? HTTPURLResponse.localizedString(forStatusCode: httpResponse.statusCode)
            throw APIClientError.server(status: httpResponse.statusCode, message: message)
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        do {
            return try decoder.decode(Response.self, from: data)
        } catch {
            throw APIClientError.invalidResponse
        }
    }
}

private struct ServerError: Decodable {
    let error: String
}
