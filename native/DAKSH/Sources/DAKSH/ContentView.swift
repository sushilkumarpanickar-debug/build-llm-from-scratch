import SwiftUI

struct ContentView: View {
    @AppStorage("tailnetBaseURL") private var tailnetBaseURL = ""
    @StateObject private var viewModel = ChatViewModel()
    @State private var isShowingSettings = false

    var body: some View {
        ChatView(viewModel: viewModel, showSettings: $isShowingSettings)
            .task {
                viewModel.configure(baseURLString: tailnetBaseURL)
                await viewModel.loadHistory()
            }
            .onChange(of: tailnetBaseURL) { _, newValue in
                viewModel.configure(baseURLString: newValue)
            }
            .sheet(isPresented: $isShowingSettings) {
                SettingsView(
                    baseURL: $tailnetBaseURL,
                    onSave: { viewModel.configure(baseURLString: tailnetBaseURL) }
                )
            }
    }
}

private struct ChatView: View {
    @ObservedObject var viewModel: ChatViewModel
    @Binding var showSettings: Bool
    @State private var draft = ""
    @State private var showClearConfirmation = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if let error = viewModel.errorMessage {
                    ErrorBanner(message: error) {
                        viewModel.errorMessage = nil
                    }
                }

                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 18) {
                            if viewModel.messages.isEmpty {
                                EmptyConversationView(isLoading: viewModel.isLoadingHistory)
                            } else {
                                ForEach(viewModel.messages) { message in
                                    MessageBubble(message: message)
                                        .id(message.id)
                                }
                            }
                            if viewModel.isSending {
                                HStack {
                                    ProgressView()
                                    Text("DAKSH is thinking…")
                                        .foregroundStyle(.secondary)
                                    Spacer()
                                }
                                .padding(.horizontal)
                            }
                        }
                        .padding(.vertical, 20)
                    }
                    .onChange(of: viewModel.messages.count) {
                        guard let last = viewModel.messages.last else { return }
                        withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                    }
                }

                Divider()
                Composer(draft: $draft, isSending: viewModel.isSending) {
                    let message = draft
                    draft = ""
                    Task { await viewModel.send(message) }
                }
            }
            .navigationTitle("DAKSH")
            .toolbar {
                ToolbarItemGroup(placement: .primaryAction) {
                    Button {
                        viewModel.startNewConversation()
                    } label: {
                        Label("New conversation", systemImage: "square.and.pencil")
                    }
                    .accessibilityLabel("New conversation")

                    Button(role: .destructive) {
                        showClearConfirmation = true
                    } label: {
                        Label("Clear conversation", systemImage: "trash")
                    }
                    .disabled(viewModel.messages.isEmpty)
                    .accessibilityLabel("Clear conversation")

                    Button {
                        showSettings = true
                    } label: {
                        Label("Endpoint settings", systemImage: "gear")
                    }
                    .accessibilityLabel("Endpoint settings")
                }
            }
            .confirmationDialog(
                "Clear this conversation?",
                isPresented: $showClearConfirmation,
                titleVisibility: .visible
            ) {
                Button("Clear messages", role: .destructive) {
                    viewModel.clearConversation()
                }
            } message: {
                Text("This only clears messages from this device's current view. Server history is unchanged.")
            }
        }
    }
}

private struct MessageBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack(alignment: .bottom) {
            if message.role == .assistant {
                Image(systemName: "sparkles")
                    .foregroundStyle(.tint)
                    .frame(width: 28, height: 28)
                    .background(.tint.opacity(0.12), in: Circle())
            } else {
                Spacer(minLength: 48)
            }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 5) {
                Text(message.text)
                    .textSelection(.enabled)
                    .padding(12)
                    .background(
                        message.role == .user ? AnyShapeStyle(Color.accentColor) : AnyShapeStyle(.quaternary),
                        in: RoundedRectangle(cornerRadius: 18, style: .continuous)
                    )
                    .foregroundStyle(message.role == .user ? .white : .primary)

                if let confidence = message.confidence {
                    Text("Confidence \(confidence.formatted(.percent.precision(.fractionLength(0))))")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }

            if message.role == .user {
                Image(systemName: "person.fill")
                    .foregroundStyle(.secondary)
                    .frame(width: 28, height: 28)
                    .background(.quaternary, in: Circle())
            } else {
                Spacer(minLength: 48)
            }
        }
        .padding(.horizontal)
    }
}

private struct Composer: View {
    @Binding var draft: String
    let isSending: Bool
    let send: () -> Void

    var body: some View {
        HStack(alignment: .bottom, spacing: 10) {
            TextField("Message DAKSH", text: $draft, axis: .vertical)
                .lineLimit(1...6)
                .textFieldStyle(.roundedBorder)
                .submitLabel(.send)
                .onSubmit(send)

            Button(action: send) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
            }
            .disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSending)
            .accessibilityLabel("Send message")
        }
        .padding()
    }
}

private struct EmptyConversationView: View {
    let isLoading: Bool

    var body: some View {
        ContentUnavailableView {
            Label("Start a conversation", systemImage: "sparkles")
        } description: {
            if isLoading {
                Text("Loading DAKSH history…")
            } else {
                Text("Ask DAKSH anything. Configure your Tailnet HTTPS endpoint in Settings.")
            }
        }
        .padding(.top, 80)
    }
}

private struct ErrorBanner: View {
    let message: String
    let dismiss: () -> Void

    var body: some View {
        HStack {
            Image(systemName: "exclamationmark.triangle.fill")
            Text(message)
                .font(.subheadline)
            Spacer()
            Button("Dismiss", action: dismiss)
                .font(.subheadline.weight(.semibold))
        }
        .padding(10)
        .foregroundStyle(.red)
        .background(.red.opacity(0.12))
    }
}

private struct SettingsView: View {
    @Binding var baseURL: String
    let onSave: () -> Void
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("DAKSH server") {
                    TextField("https://daksh.your-tailnet.ts.net", text: $baseURL)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        #endif
                        .autocorrectionDisabled()
                    Text("Use the HTTPS URL of the DAKSH web dashboard reachable from your Tailnet. No API keys are stored in this app.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Endpoint Settings")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        onSave()
                        dismiss()
                    }
                }
            }
        }
    }
}
