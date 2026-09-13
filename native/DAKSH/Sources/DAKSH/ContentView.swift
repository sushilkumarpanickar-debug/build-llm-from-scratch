import SwiftUI

#if SWIFT_PACKAGE
private let dakshLogoBundle = Bundle.module
#else
private let dakshLogoBundle = Bundle.main
#endif

struct ContentView: View {
    @AppStorage("tailnetBaseURL") private var tailnetBaseURL = ""
    @StateObject private var viewModel = ChatViewModel()
    @State private var isShowingSettings = false
    @State private var isShowingMemory = false

    var body: some View {
        NavigationSplitView {
            CommandSidebar(
                messageCount: viewModel.messages.count,
                isSending: viewModel.isSending,
                showSettings: $isShowingSettings,
                newConversation: viewModel.startNewConversation
            )
        } detail: {
            CommandCenter(
                viewModel: viewModel,
                showSettings: $isShowingSettings,
                showMemory: $isShowingMemory
            )
        }
        .task {
            #if os(macOS)
            if tailnetBaseURL.isEmpty {
                tailnetBaseURL = "http://127.0.0.1:9000"
            }
            #endif
            viewModel.configure(baseURLString: tailnetBaseURL)
            await viewModel.loadHistory()
            while !Task.isCancelled {
                await viewModel.refreshStatus()
                try? await Task.sleep(for: .seconds(5))
            }
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
        .sheet(isPresented: $isShowingMemory) {
            MemoryCaptureView(viewModel: viewModel)
        }
    }
}

private struct CommandSidebar: View {
    let messageCount: Int
    let isSending: Bool
    @Binding var showSettings: Bool
    let newConversation: () -> Void

    var body: some View {
        List {
            Section {
                Label("Command Center", systemImage: "rectangle.3.group.fill")
                Label("AI Core", systemImage: "cpu")
                Label("Memory", systemImage: "brain.head.profile")
                Label("Conversations (\(messageCount))", systemImage: "bubble.left.and.bubble.right")
                Label("Tools & Skills", systemImage: "wrench.and.screwdriver")
            } header: {
                VStack(alignment: .leading, spacing: 3) {
                    Text("DAKSH AI").font(.title3.weight(.bold))
                    Text(isSending ? "PROCESSING" : "LOCAL SYSTEM READY")
                        .font(.caption2.weight(.semibold))
                        .foregroundStyle(isSending ? .orange : .green)
                }
                .padding(.vertical, 10)
            }

            Section("Voice") {
                Label("Push-to-talk enabled", systemImage: "waveform")
                    .foregroundStyle(.cyan)
            }

            Section {
                Button(action: newConversation) {
                    Label("New conversation", systemImage: "square.and.pencil")
                }
                Button { showSettings = true } label: {
                    Label("Connection settings", systemImage: "gearshape")
                }
            }
        }
        .navigationTitle("DAKSH AI")
    }
}

private struct CommandCenter: View {
    @ObservedObject var viewModel: ChatViewModel
    @Binding var showSettings: Bool
    @Binding var showMemory: Bool
    @StateObject private var voiceInput = VoiceInputController()
    @State private var draft = ""
    @State private var showClearConfirmation = false

    var body: some View {
        VStack(spacing: 0) {
            if let error = viewModel.errorMessage {
                ErrorBanner(message: error) { viewModel.errorMessage = nil }
            }
            if let error = voiceInput.errorMessage {
                ErrorBanner(message: error) { voiceInput.errorMessage = nil }
            }

            ScrollViewReader { proxy in
                ScrollView {
                    VStack(spacing: 20) {
                        CoreHero(isProcessing: viewModel.isSending, isConnected: viewModel.isConnected)
                        StatusGrid(
                            status: viewModel.systemStatus,
                            brain: viewModel.brainStatus,
                            isProcessing: viewModel.isSending,
                            isConnected: viewModel.isConnected,
                            showSettings: $showSettings,
                            showMemory: $showMemory
                        )
                        ConversationPanel(
                            messages: viewModel.messages,
                            isLoading: viewModel.isLoadingHistory,
                            isSending: viewModel.isSending
                        )
                    }
                    .padding()
                }
                .onChange(of: viewModel.messages.count) {
                    guard let last = viewModel.messages.last else { return }
                    withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                }
            }

            CommandComposer(draft: $draft, isSending: viewModel.isSending, voiceInput: voiceInput) {
                let message = draft
                draft = ""
                Task { await viewModel.send(message) }
            }
        }
        .background(
            LinearGradient(
                colors: [Color(red: 0.02, green: 0.06, blue: 0.12), Color(red: 0.02, green: 0.12, blue: 0.18)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .navigationTitle("DAKSH AI")
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                Button {
                    viewModel.startNewConversation()
                } label: {
                    Label("New conversation", systemImage: "square.and.pencil")
                }
                Button(role: .destructive) {
                    showClearConfirmation = true
                } label: {
                    Label("Clear conversation", systemImage: "trash")
                }
                .disabled(viewModel.messages.isEmpty)
            }
        }
        .confirmationDialog("Clear this conversation?", isPresented: $showClearConfirmation) {
            Button("Clear messages", role: .destructive) {
                viewModel.clearConversation()
            }
        } message: {
            Text("This clears the current app view. Server history remains private in iCloud Drive.")
        }
    }
}

private struct CoreHero: View {
    let isProcessing: Bool
    let isConnected: Bool

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(.ultraThinMaterial)
                .overlay(RoundedRectangle(cornerRadius: 24).stroke(.cyan.opacity(0.35)))
            HStack(spacing: 24) {
                ZStack {
                    Circle().stroke(.cyan.opacity(0.25), lineWidth: 22).frame(width: 126, height: 126)
                    Circle().trim(from: 0.08, to: isProcessing ? 0.94 : 0.72).stroke(.cyan, style: StrokeStyle(lineWidth: 4, lineCap: .round)).rotationEffect(.degrees(-90)).frame(width: 104, height: 104)
                    Image("daksh-mark", bundle: dakshLogoBundle)
                        .resizable()
                        .scaledToFit()
                        .padding(10)
                        .symbolEffect(.pulse, isActive: isProcessing)
                }
                VStack(alignment: .leading, spacing: 6) {
                    Text("DAKSH AI").font(.system(size: 32, weight: .bold, design: .rounded)).foregroundStyle(.white)
                    Text(isProcessing ? "PROCESSING YOUR REQUEST" : (isConnected ? "PRIVATE LOCAL AI CORE" : "CONNECTING TO DAKSH"))
                        .font(.caption.weight(.bold)).tracking(1.4).foregroundStyle(.cyan)
                    Text("Local model · iCloud memory · Tailnet access")
                        .font(.subheadline).foregroundStyle(.white.opacity(0.72))
                }
                Spacer()
            }
            .padding(24)
        }
        .frame(maxWidth: 900)
    }
}

private struct StatusGrid: View {
    let status: DashboardStatus?
    let brain: BrainStatus?
    let isProcessing: Bool
    let isConnected: Bool
    @Binding var showSettings: Bool
    @Binding var showMemory: Bool

    var body: some View {
        ViewThatFits {
            HStack(spacing: 14) { cards }
            VStack(spacing: 14) { cards }
        }
    }

    @ViewBuilder private var cards: some View {
        StatusCard(title: "AI Core", value: isProcessing ? "Working" : (isConnected ? "Ready" : "Offline"), icon: "cpu.fill", color: .cyan)
        StatusCard(title: "Memory", value: "\(status?.contextSize ?? 0) records", icon: "brain.head.profile", color: .mint)
        Button { showMemory = true } label: {
            StatusCard(title: "Second Brain", value: "\(brain?.knowledgeGraph?.totalDocuments ?? 0) documents", icon: "brain.head.profile", color: .mint)
        }
        .buttonStyle(.plain)
        StatusCard(title: "Skills", value: "\(brain?.skillRouter?.totalSkills ?? 0) ready", icon: "wand.and.stars", color: .purple)
        StatusCard(title: "Workers", value: "\(brain?.commander?.workers ?? 0) online", icon: "person.3.fill", color: .blue)
        Button { showSettings = true } label: {
            StatusCard(title: "Network", value: isConnected ? "Connected" : "Unavailable", icon: "lock.shield.fill", color: isConnected ? .green : .orange)
        }
        .buttonStyle(.plain)
    }
}

private struct StatusCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon).foregroundStyle(color).font(.title3)
            VStack(alignment: .leading) {
                Text(title).font(.caption).foregroundStyle(.secondary)
                Text(value).font(.subheadline.weight(.semibold)).foregroundStyle(.primary)
            }
            Spacer(minLength: 0)
        }
        .padding(14)
        .frame(maxWidth: .infinity)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(color.opacity(0.2)))
    }
}

private struct ConversationPanel: View {
    let messages: [ChatMessage]
    let isLoading: Bool
    let isSending: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Label("Conversation", systemImage: "bubble.left.and.bubble.right.fill")
                .font(.headline).foregroundStyle(.white)
            if messages.isEmpty {
                ContentUnavailableView {
                    Label("Ready for your command", systemImage: "sparkles")
                } description: {
                    Text(isLoading ? "Loading DAKSH memory…" : "Ask DAKSH AI a question or use push-to-talk.")
                }
                .foregroundStyle(.white.opacity(0.75))
                .frame(maxWidth: .infinity, minHeight: 200)
            } else {
                ForEach(messages) { message in
                    MessageBubble(message: message).id(message.id)
                }
            }
            if isSending {
                Label("DAKSH AI is thinking…", systemImage: "ellipsis.message")
                    .foregroundStyle(.cyan)
            }
        }
        .padding()
        .frame(maxWidth: 900, alignment: .leading)
        .background(.black.opacity(0.16), in: RoundedRectangle(cornerRadius: 20))
    }
}

private struct MessageBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack(alignment: .top) {
            Image(systemName: message.role == .user ? "person.fill" : "sparkles")
                .foregroundStyle(message.role == .user ? .white : .cyan)
                .frame(width: 30, height: 30)
                .background(message.role == .user ? .blue : .cyan.opacity(0.16), in: Circle())
            VStack(alignment: .leading, spacing: 5) {
                Text(message.role == .user ? "YOU" : "DAKSH AI").font(.caption2.weight(.bold)).foregroundStyle(.cyan)
                Text(message.text).textSelection(.enabled).foregroundStyle(.white)
                if let confidence = message.confidence {
                    Text("Confidence \(confidence.formatted(.percent.precision(.fractionLength(0))))")
                        .font(.caption2).foregroundStyle(.white.opacity(0.55))
                }
            }
            Spacer()
        }
        .padding(12)
        .background(message.role == .user ? .blue.opacity(0.16) : .white.opacity(0.06), in: RoundedRectangle(cornerRadius: 14))
    }
}

private struct CommandComposer: View {
    @Binding var draft: String
    let isSending: Bool
    @ObservedObject var voiceInput: VoiceInputController
    let send: () -> Void

    var body: some View {
        HStack(alignment: .bottom, spacing: 10) {
            Button { voiceInput.toggle() } label: {
                Image(systemName: voiceInput.isListening ? "stop.circle.fill" : "mic.circle.fill").font(.title)
            }
            .tint(voiceInput.isListening ? .red : .cyan)
            .disabled(isSending)

            TextField(voiceInput.isListening ? "Listening…" : "Give DAKSH AI a command", text: $draft, axis: .vertical)
                .lineLimit(1...5)
                .textFieldStyle(.plain)
                .foregroundStyle(.white)
                .onChange(of: voiceInput.transcript) { _, transcript in draft = transcript }
                .onSubmit(send)

            Button(action: send) {
                Image(systemName: "arrow.up.circle.fill").font(.title)
            }
            .disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSending)
        }
        .padding(14)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
        .overlay(RoundedRectangle(cornerRadius: 20).stroke(.cyan.opacity(0.35)))
        .padding()
    }
}

private struct ErrorBanner: View {
    let message: String
    let dismiss: () -> Void

    var body: some View {
        HStack {
            Image(systemName: "exclamationmark.triangle.fill")
            Text(message).font(.subheadline)
            Spacer()
            Button("Dismiss", action: dismiss).font(.subheadline.weight(.semibold))
        }
        .padding(10).foregroundStyle(.red).background(.red.opacity(0.12))
    }
}

private struct SettingsView: View {
    @Binding var baseURL: String
    let onSave: () -> Void
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("DAKSH AI private server") {
                    TextField("https://daksh.your-tailnet.ts.net", text: $baseURL)
                        #if os(iOS)
                        .textInputAutocapitalization(.never).keyboardType(.URL)
                        #endif
                        .autocorrectionDisabled()
                    Text("On this Mac, use http://127.0.0.1:9000. On iPhone, use the HTTPS URL supplied by Tailscale Serve. No API keys are stored in this app.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Connection settings")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) { Button("Save") { onSave(); dismiss() } }
            }
        }
    }
}

private struct MemoryCaptureView: View {
    @ObservedObject var viewModel: ChatViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var content = ""
    @State private var isSaving = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Private second brain") {
                    TextField("Title", text: $title)
                    TextEditor(text: $content)
                        .frame(minHeight: 160)
                    Text("Saved only to the DAKSH private data store and used as a cited context source when relevant.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Save memory")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        isSaving = true
                        Task {
                            if await viewModel.saveMemory(title: title, content: content) {
                                dismiss()
                            }
                            isSaving = false
                        }
                    }
                    .disabled(
                        isSaving
                            || title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                            || content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                    )
                }
            }
        }
    }
}
