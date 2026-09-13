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

struct HistoryInteraction: Decodable, Identifiable, Sendable {
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

struct DashboardStatus: Decodable, Sendable {
    let cloudFallbackEnabled: Bool
    let contextSize: Int
    let interactions: Int
    let status: String

    enum CodingKeys: String, CodingKey {
        case cloudFallbackEnabled = "cloud_fallback_enabled"
        case contextSize = "context_size"
        case interactions, status
    }
}

struct BrainStatus: Decodable, Sendable {
    let knowledgeGraph: KnowledgeGraphStatus?
    let skillRouter: SkillRouterStatus?
    let commander: CommanderStatus?

    enum CodingKeys: String, CodingKey {
        case knowledgeGraph = "knowledge_graph"
        case skillRouter = "skill_router"
        case commander
    }
}

struct KnowledgeGraphStatus: Decodable, Sendable {
    let totalDocuments: Int

    enum CodingKeys: String, CodingKey {
        case totalDocuments = "total_documents"
    }
}

struct SkillRouterStatus: Decodable, Sendable {
    let totalSkills: Int

    enum CodingKeys: String, CodingKey {
        case totalSkills = "total_skills"
    }
}

struct CommanderStatus: Decodable, Sendable {
    let workers: Int
}

struct MemoryDocumentRequest: Encodable, Sendable {
    let title: String
    let content: String
    let source = "DAKSH native app"
}

struct DocumentsResponse: Decodable, Sendable {
    let documents: [BrainDocument]
}

struct BrainDocument: Decodable, Identifiable, Sendable {
    let id: String
    let title: String
    let source: String
    let chunks: Int
    let entities: Int
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, title, source, chunks, entities
        case createdAt = "created_at"
    }
}

struct SkillsResponse: Decodable, Sendable {
    let skills: [RegisteredSkill]
}

struct RegisteredSkill: Decodable, Identifiable, Sendable {
    let slug: String
    let name: String
    let description: String
    let type: String
    let version: String
    let inputSchema: [String: String]
    let sideEffectFree: Bool

    var id: String { slug }

    enum CodingKeys: String, CodingKey {
        case slug, name, description, type, version
        case inputSchema = "input_schema"
        case sideEffectFree = "side_effect_free"
    }
}

struct SkillExecutionRequest: Encodable, Sendable {
    let skill: String
    let input: [String: String]
}
