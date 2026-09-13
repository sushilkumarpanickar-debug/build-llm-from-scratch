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

    func loadStatus() async throws -> DashboardStatus {
        try await perform(URLRequest(url: endpoint(path: "api/daksh/status")))
    }

    func loadBrainStatus() async throws -> BrainStatus {
        try await perform(URLRequest(url: endpoint(path: "api/brain/status")))
    }

    func saveMemory(title: String, content: String) async throws {
        var request = URLRequest(url: endpoint(path: "api/brain/documents"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(
            MemoryDocumentRequest(title: title, content: content)
        )
        let _: EmptyResponse = try await perform(request)
    }

    func loadDocuments() async throws -> [BrainDocument] {
        let response: DocumentsResponse = try await perform(
            URLRequest(url: endpoint(path: "api/brain/documents"))
        )
        return response.documents
    }

    func loadSkills() async throws -> [RegisteredSkill] {
        let response: SkillsResponse = try await perform(
            URLRequest(url: endpoint(path: "api/skills"))
        )
        return response.skills
    }

    func runTextCleanup(_ text: String) async throws -> String {
        var request = URLRequest(url: endpoint(path: "api/skills"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(
            SkillExecutionRequest(
                skill: "text-processing",
                input: ["text": text, "action": "clean"]
            )
        )
        let response: SkillExecutionResponse = try await perform(request)
        return response.finalOutput.cleanedText
    }

    func importDocument(filename: String, content: Data) async throws {
        let boundary = "DakshBoundary-\(UUID().uuidString)"
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"document\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
        body.append(content)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        var request = URLRequest(url: endpoint(path: "api/brain/import"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = body
        let _: EmptyResponse = try await perform(request)
    }
    private func endpoint(path: String) -> URL {
        baseURL.appending(path: path)
    }

    private struct EmptyResponse: Decodable {}

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

private struct SkillExecutionResponse: Decodable {
    let finalOutput: CleanTextOutput

    enum CodingKeys: String, CodingKey {
        case finalOutput = "final_output"
    }

    struct CleanTextOutput: Decodable {
        fileprivate let cleanedText: String

        enum CodingKeys: String, CodingKey {
            case cleanedText = "cleaned_text"
        }
    }
}
