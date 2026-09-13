import Foundation

@MainActor
final class ChatViewModel: ObservableObject {
    @Published private(set) var messages: [ChatMessage] = []
    @Published private(set) var isLoadingHistory = false
    @Published private(set) var isSending = false
    @Published var errorMessage: String?
    @Published private(set) var hasLoadedHistory = false

    private var client: APIClient?

    init(baseURLString: String = UserDefaults.standard.string(forKey: "tailnetBaseURL") ?? "") {
        configure(baseURLString: baseURLString)
    }

    func configure(baseURLString: String) {
        do {
            client = try APIClient(baseURLString: baseURLString)
            errorMessage = nil
        } catch {
            client = nil
        }
    }

    func loadHistory() async {
        guard let client else { return }
        isLoadingHistory = true
        defer {
            isLoadingHistory = false
            hasLoadedHistory = true
        }

        do {
            let history = try await client.loadHistory()
            messages = history.flatMap { interaction in
                [
                    ChatMessage(
                        id: "\(interaction.id)-user",
                        role: .user,
                        text: interaction.input,
                        date: interaction.time
                    ),
                    ChatMessage(
                        id: "\(interaction.id)-assistant",
                        role: .assistant,
                        text: interaction.response,
                        date: interaction.time,
                        confidence: interaction.confidence
                    )
                ]
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func send(_ text: String) async {
        let input = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !input.isEmpty, !isSending else { return }
        guard let client else {
            errorMessage = APIClientError.invalidBaseURL.localizedDescription
            return
        }

        isSending = true
        errorMessage = nil
        messages.append(ChatMessage(role: .user, text: input))
        defer { isSending = false }

        do {
            let response = try await client.send(input: input)
            messages.append(
                ChatMessage(
                    id: "\(response.id)-assistant",
                    role: .assistant,
                    text: response.response,
                    confidence: response.confidence,
                    timeMilliseconds: response.timeMilliseconds
                )
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func startNewConversation() {
        messages = []
        errorMessage = nil
    }

    func clearConversation() {
        messages = []
        errorMessage = nil
    }
}
