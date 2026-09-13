import Foundation

enum MessageRole: String, Codable, Sendable {
    case user
    case assistant
}

struct ChatMessage: Identifiable, Equatable, Sendable {
    let id: String
    let role: MessageRole
    let text: String
    let date: Date
    let confidence: Double?
    let timeMilliseconds: Double?

    init(
        id: String = UUID().uuidString,
        role: MessageRole,
        text: String,
        date: Date = .now,
        confidence: Double? = nil,
        timeMilliseconds: Double? = nil
    ) {
        self.id = id
        self.role = role
        self.text = text
        self.date = date
        self.confidence = confidence
        self.timeMilliseconds = timeMilliseconds
    }
}

struct InteractionHistoryResponse: Decodable, Sendable {
    let history: [HistoryInteraction]
}

struct HistoryInteraction: Decodable, Sendable {
    let id: String
    let input: String
    let response: String
    let time: Date
    let confidence: Double?
}

struct InteractionResponse: Decodable, Sendable {
    let id: String
    let input: String
    let response: String
    let confidence: Double?
    let timeMilliseconds: Double?

    enum CodingKeys: String, CodingKey {
        case id, input, response, confidence
        case timeMilliseconds = "time_ms"
    }
}

struct InteractionRequest: Encodable, Sendable {
    let input: String
    let type = "text"
}
