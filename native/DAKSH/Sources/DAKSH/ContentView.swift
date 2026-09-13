import SwiftUI
import UniformTypeIdentifiers

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
    @State private var section: AppSection? = .chat

    var body: some View {
        NavigationSplitView {
            CommandSidebar(
                messageCount: viewModel.messages.count,
                isSending: viewModel.isSending,
                history: viewModel.history,
                selection: $section,
                showSettings: $isShowingSettings,
                newConversation: {
                    viewModel.startNewConversation()
                    section = .chat
                },
                selectHistory: {
                    viewModel.showHistoryItem($0)
                    section = .chat
                }
            )
        } detail: {
            detailView
                #if os(macOS)
                .frame(minWidth: 760, minHeight: 620)
                #endif
        }
        .navigationSplitViewStyle(.balanced)
        .preferredColorScheme(.dark)
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

    @ViewBuilder private var detailView: some View {
        switch section ?? .chat {
        case .chat:
            CommandCenter(viewModel: viewModel, showSettings: $isShowingSettings, showMemory: $isShowingMemory)
        case .memory:
            MemoryWorkspace(viewModel: viewModel, showMemory: $isShowingMemory)
        case .documents:
            DocumentsWorkspace(viewModel: viewModel)
        case .skills:
            SkillsWorkspace(viewModel: viewModel)
        case .system:
            SystemWorkspace(viewModel: viewModel, showSettings: $isShowingSettings)
        }
    }
}

private enum AppSection: String, CaseIterable, Hashable {
    case chat = "Chat"
    case memory = "Memory"
    case documents = "Documents"
    case skills = "Skills"
    case system = "System"

    var icon: String {
        switch self {
        case .chat: "bubble.left.and.bubble.right.fill"
        case .memory: "brain.head.profile.fill"
        case .documents: "folder.fill"
        case .skills: "wand.and.stars"
        case .system: "cpu.fill"
        }
    }
}

private struct CommandSidebar: View {
    let messageCount: Int
    let isSending: Bool
    let history: [HistoryInteraction]
    @Binding var selection: AppSection?
    @Binding var showSettings: Bool
    let newConversation: () -> Void
    let selectHistory: (HistoryInteraction) -> Void

    var body: some View {
        List(selection: $selection) {
            Section {
                ForEach(AppSection.allCases, id: \.self) { item in
                    Label(item.rawValue, systemImage: item.icon).tag(item)
                }
            } header: {
                VStack(alignment: .leading, spacing: 3) {
                    Text("DAKSH AI").font(.title3.weight(.bold))
                    Text(isSending ? "PROCESSING" : "LOCAL SYSTEM READY")
                        .font(.caption2.weight(.semibold))
                        .foregroundStyle(isSending ? .orange : .green)
                }
                .padding(.vertical, 10)
            }

            Section("Recent requests") {
                if history.isEmpty {
                    Text("Your private history will appear here.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(history.suffix(12).reversed()) { interaction in
                        Button {
                            selectHistory(interaction)
                        } label: {
                            Label(interaction.input, systemImage: "bubble.left")
                                .lineLimit(1)
                        }
                        .buttonStyle(.plain)
                    }
                }
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
    @State private var isShowingVoiceConsole = false

    private func submit(_ command: String) {
        let input = command.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !input.isEmpty, !viewModel.isSending else { return }
        draft = ""
        Task { await viewModel.send(input) }
    }

    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
            if let error = viewModel.errorMessage {
                ErrorBanner(message: error) { viewModel.errorMessage = nil }
            }
            if let error = voiceInput.errorMessage {
                ErrorBanner(message: error) { voiceInput.errorMessage = nil }
            }

                ScrollViewReader { proxy in
                    ScrollView {
                        VStack(spacing: 16) {
                            CoreHero(
                                isProcessing: viewModel.isSending,
                                isConnected: viewModel.isConnected,
                                messageCount: viewModel.messages.count
                            )
                            if geometry.size.width >= 920 {
                                HStack(alignment: .top, spacing: 16) {
                                    cockpitMain(proxy: proxy)
                                    ActivityRail(
                                        messages: viewModel.messages,
                                        status: viewModel.systemStatus,
                                        brain: viewModel.brainStatus,
                                        isConnected: viewModel.isConnected
                                    )
                                    .frame(width: 260)
                                }
                            } else {
                                cockpitMain(proxy: proxy)
                                ActivityRail(
                                    messages: viewModel.messages,
                                    status: viewModel.systemStatus,
                                    brain: viewModel.brainStatus,
                                    isConnected: viewModel.isConnected
                                )
                            }
                        }
                        .padding(16)
                    }
                    .onChange(of: viewModel.messages.count) {
                        guard let last = viewModel.messages.last else { return }
                        withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                    }
                }
                CommandComposer(draft: $draft, isSending: viewModel.isSending, voiceInput: voiceInput) {
                    submit(draft)
                }
            }
            .background(HUDBackground())
        }
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
        .sheet(isPresented: $isShowingVoiceConsole) {
            VoiceConsole(
            voiceInput: voiceInput,
            isSending: viewModel.isSending,
            dismiss: { isShowingVoiceConsole = false },
            send: { submit(voiceInput.transcript) }
            )
            #if os(macOS)
            .frame(minWidth: 760, minHeight: 620)
            #endif
        }
    }

    @ViewBuilder private func cockpitMain(proxy: ScrollViewProxy) -> some View {
        VStack(spacing: 16) {
            QuickCommandDeck(
            isSending: viewModel.isSending,
            openMemory: { showMemory = true },
            openVoice: { isShowingVoiceConsole = true },
            send: submit
            )
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
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct CoreHero: View {
    let isProcessing: Bool
    let isConnected: Bool
    let messageCount: Int

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(.ultraThinMaterial)
                .overlay(RoundedRectangle(cornerRadius: 20).stroke(.cyan.opacity(0.35)))
            HStack(spacing: 14) {
                ZStack {
                    Circle().stroke(.cyan.opacity(0.25), lineWidth: 12).frame(width: 68, height: 68)
                    Circle().trim(from: 0.08, to: isProcessing ? 0.94 : 0.72).stroke(.cyan, style: StrokeStyle(lineWidth: 3, lineCap: .round)).rotationEffect(.degrees(-90)).frame(width: 58, height: 58)
                    Image("daksh-mark", bundle: dakshLogoBundle)
                        .resizable()
                        .scaledToFit()
                        .padding(6)
                        .symbolEffect(.pulse, isActive: isProcessing)
                }
                VStack(alignment: .leading, spacing: 3) {
                    Text("DAKSH AI").font(.title2.weight(.bold)).foregroundStyle(.white)
                    Text(isProcessing ? "PROCESSING YOUR REQUEST" : (isConnected ? "PRIVATE LOCAL AI CORE" : "CONNECTING TO DAKSH"))
                        .font(.caption.weight(.bold)).tracking(1.4).foregroundStyle(.cyan)
                    Text("\(messageCount) messages in this session · local model · private memory")
                        .font(.caption).foregroundStyle(.white.opacity(0.72))
                }
                Spacer()
                Image(systemName: isConnected ? "lock.shield.fill" : "exclamationmark.triangle.fill")
                    .foregroundStyle(isConnected ? .mint : .orange)
                    .font(.title2)
            }
            .padding(16)
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
        StatusCard(title: "Memory", value: "\(brain?.knowledgeGraph?.totalDocuments ?? status?.contextSize ?? 0) records", icon: "brain.head.profile", color: .mint)
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

private struct QuickCommandDeck: View {
    let isSending: Bool
    let openMemory: () -> Void
    let openVoice: () -> Void
    let send: (String) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Label("COMMAND DECK", systemImage: "bolt.horizontal.circle.fill")
                    .font(.caption.weight(.bold)).tracking(1.1).foregroundStyle(.cyan)
                Spacer()
                Text("LOCAL + PRIVATE").font(.caption2.weight(.bold)).foregroundStyle(.mint)
            }
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 145), spacing: 10)], spacing: 10) {
                DeckButton(title: "System report", icon: "gauge.with.dots.needle.67percent", color: .cyan) {
                    send("Give me a concise status report of DAKSH and my private second brain.")
                }
                DeckButton(title: "Search memory", icon: "magnifyingglass.circle.fill", color: .mint) {
                    send("What do you know from my private DAKSH memory?")
                }
                DeckButton(title: "Plan a task", icon: "checklist.checked", color: .purple) {
                    send("Help me create a clear plan for my next task.")
                }
                DeckButton(title: "Save memory", icon: "plus.circle.fill", color: .orange, action: openMemory)
                DeckButton(title: "Voice console", icon: "waveform.circle.fill", color: .pink, action: openVoice)
            }
        }
        .padding(15)
        .background(.black.opacity(0.22), in: RoundedRectangle(cornerRadius: 18))
        .overlay(RoundedRectangle(cornerRadius: 18).stroke(.cyan.opacity(0.26)))
        .disabled(isSending)
    }
}

private struct DeckButton: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 9) {
                Image(systemName: icon).foregroundStyle(color)
                Text(title).font(.caption.weight(.semibold)).lineLimit(1)
                Spacer(minLength: 0)
            }
            .padding(11)
            .background(color.opacity(0.1), in: RoundedRectangle(cornerRadius: 12))
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(color.opacity(0.28)))
        }
        .buttonStyle(.plain)
        .foregroundStyle(.white)
    }
}

private struct ActivityRail: View {
    let messages: [ChatMessage]
    let status: DashboardStatus?
    let brain: BrainStatus?
    let isConnected: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 13) {
            Label("LIVE ACTIVITY", systemImage: "dot.radiowaves.left.and.right")
                .font(.caption.weight(.bold)).tracking(1.1).foregroundStyle(.cyan)
            RailMetric("CONNECTION", isConnected ? "SECURE LOCAL" : "OFFLINE", isConnected ? .mint : .orange)
            RailMetric("INTERACTIONS", "\(status?.interactions ?? 0)", .cyan)
            RailMetric("DOCUMENTS", "\(brain?.knowledgeGraph?.totalDocuments ?? 0)", .mint)
            Divider().overlay(.white.opacity(0.15))
            Text("RECENT SIGNALS").font(.caption2.weight(.bold)).foregroundStyle(.white.opacity(0.55))
            if messages.isEmpty {
                Text("Awaiting your first command.").font(.caption).foregroundStyle(.white.opacity(0.65))
            } else {
                ForEach(messages.suffix(4).reversed()) { message in
                    HStack(alignment: .top, spacing: 8) {
                        Circle().fill(message.role == .assistant ? .cyan : .blue).frame(width: 6, height: 6).padding(.top, 5)
                        Text(message.text).font(.caption).lineLimit(3).foregroundStyle(.white.opacity(0.78))
                    }
                }
            }
        }
        .padding(15)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.black.opacity(0.22), in: RoundedRectangle(cornerRadius: 18))
        .overlay(RoundedRectangle(cornerRadius: 18).stroke(.cyan.opacity(0.22)))
    }
}

private struct RailMetric: View {
    let label: String
    let value: String
    let color: Color

    init(_ label: String, _ value: String, _ color: Color) {
        self.label = label; self.value = value; self.color = color
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(label).font(.caption2.weight(.bold)).tracking(0.8).foregroundStyle(.white.opacity(0.5))
            Text(value).font(.caption.weight(.bold)).foregroundStyle(color)
        }
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

private struct VoiceConsole: View {
    @ObservedObject var voiceInput: VoiceInputController
    let isSending: Bool
    let dismiss: () -> Void
    let send: () -> Void
    @State private var isOrbiting = false

    private var status: String {
        if isSending { return "PROCESSING YOUR REQUEST" }
        if voiceInput.isListening { return "LISTENING" }
        if voiceInput.transcript.isEmpty { return "VOICE CONSOLE READY" }
        return "REVIEW TRANSCRIPT"
    }

    var body: some View {
        ZStack {
            HUDBackground()
            VStack(spacing: 28) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("DAKSH AI").font(.headline.weight(.bold)).tracking(2).foregroundStyle(.white)
                        Text("PRIVATE VOICE CONSOLE").font(.caption2.weight(.bold)).tracking(1.1).foregroundStyle(.cyan)
                    }
                    Spacer()
                    Button("Close", systemImage: "xmark.circle.fill", action: dismiss)
                        .labelStyle(.iconOnly).font(.title2).foregroundStyle(.white.opacity(0.8))
                }
                Spacer()
                ZStack {
                    Circle().stroke(.cyan.opacity(0.12), lineWidth: 1).frame(width: 300, height: 300)
                    Circle().stroke(.cyan.opacity(0.24), lineWidth: 2).frame(width: 238, height: 238)
                        .rotationEffect(.degrees(isOrbiting ? 360 : 0))
                    Circle().trim(from: 0.07, to: voiceInput.isListening ? 0.92 : 0.66)
                        .stroke(voiceInput.isListening ? .pink : .cyan, style: StrokeStyle(lineWidth: 5, lineCap: .round))
                        .frame(width: 184, height: 184).rotationEffect(.degrees(-90))
                    Image("daksh-mark", bundle: dakshLogoBundle)
                        .resizable().scaledToFit().frame(width: 126, height: 126)
                        .scaleEffect(voiceInput.isListening ? 1.08 : 1)
                        .animation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true), value: voiceInput.isListening)
                }
                .animation(.linear(duration: 12).repeatForever(autoreverses: false), value: isOrbiting)
                Text(status).font(.caption.weight(.bold)).tracking(2).foregroundStyle(voiceInput.isListening ? .pink : .cyan)
                Text(voiceInput.transcript.isEmpty ? "Tap the microphone and speak naturally." : voiceInput.transcript)
                    .font(.title3).multilineTextAlignment(.center).foregroundStyle(.white)
                    .frame(maxWidth: 620, minHeight: 56)
                HStack(spacing: 16) {
                    Button {
                        voiceInput.toggle()
                    } label: {
                        Label(voiceInput.isListening ? "Stop listening" : "Speak", systemImage: voiceInput.isListening ? "stop.fill" : "mic.fill")
                            .frame(minWidth: 130)
                    }
                    .buttonStyle(.borderedProminent).tint(voiceInput.isListening ? .pink : .cyan)
                    .disabled(isSending)
                    Button("Send", systemImage: "arrow.up.circle.fill", action: send)
                        .buttonStyle(.bordered)
                        .disabled(voiceInput.transcript.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSending)
                }
                Spacer()
                Text("Speech is captured on this device. DAKSH does not send a request until you select Send.")
                    .font(.caption).foregroundStyle(.white.opacity(0.58))
            }
            .padding(28)
        }
        .onAppear { isOrbiting = true }
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

private struct MemoryWorkspace: View {
    @ObservedObject var viewModel: ChatViewModel
    @Binding var showMemory: Bool

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                WorkspaceHeader(
                    eyebrow: "PRIVATE CONTEXT",
                    title: "Second Brain",
                    subtitle: "Confirmed notes and imported source material stored in your private DAKSH data directory."
                ) {
                    Button("Save memory", systemImage: "plus.circle.fill") { showMemory = true }
                        .buttonStyle(.borderedProminent)
                        .tint(.cyan)
                }
                MetricRow(values: [
                    ("Documents", "\(viewModel.documents.count)", "folder.fill", .mint),
                    ("Conversations", "\(viewModel.history.count)", "bubble.left.and.bubble.right.fill", .cyan),
                    ("Skills", "\(viewModel.skills.count)", "wand.and.stars", .purple),
                ])
                if viewModel.documents.isEmpty {
                    ContentUnavailableView(
                        "Your second brain is empty",
                        systemImage: "brain.head.profile",
                        description: Text("Save a note or import a document to create a private, source-traceable memory.")
                    )
                    .frame(maxWidth: .infinity, minHeight: 260)
                } else {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("RECENT KNOWLEDGE").font(.caption.weight(.bold)).tracking(1.2).foregroundStyle(.cyan)
                        ForEach(viewModel.documents) { document in
                            DocumentRow(document: document)
                        }
                    }
                }
            }
            .padding(24)
        }
        .background(HUDBackground())
        .navigationTitle("Second Brain")
    }
}

private struct DocumentsWorkspace: View {
    @ObservedObject var viewModel: ChatViewModel
    @State private var isImporting = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                WorkspaceHeader(
                    eyebrow: "PRIVATE FILE VAULT",
                    title: "Documents",
                    subtitle: "DAKSH processes only files you explicitly choose. It never scans your device."
                ) {
                    Button("Import document", systemImage: "square.and.arrow.down") { isImporting = true }
                        .buttonStyle(.borderedProminent)
                        .tint(.cyan)
                }
                Text("Supported: TXT, Markdown, CSV, JSON, DOCX, and text PDFs. Files are extracted locally and limited to 10 MB by default.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .padding(14)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 16))
                if viewModel.documents.isEmpty {
                    ContentUnavailableView(
                        "No documents imported",
                        systemImage: "doc.badge.plus",
                        description: Text("Choose a file to make it available as cited DAKSH context.")
                    )
                    .frame(maxWidth: .infinity, minHeight: 260)
                } else {
                    LazyVStack(spacing: 10) {
                        ForEach(viewModel.documents) { document in
                            DocumentRow(document: document)
                        }
                    }
                }
            }
            .padding(24)
        }
        .background(HUDBackground())
        .navigationTitle("Documents")
        .fileImporter(
            isPresented: $isImporting,
            allowedContentTypes: [.plainText, .commaSeparatedText, .pdf, .json, .data],
            allowsMultipleSelection: false
        ) { result in
            if case let .success(urls) = result, let url = urls.first {
                Task { await viewModel.importDocument(url: url) }
            } else if case let .failure(error) = result {
                viewModel.errorMessage = error.localizedDescription
            }
        }
    }
}

private struct SkillsWorkspace: View {
    @ObservedObject var viewModel: ChatViewModel
    @State private var input = ""
    @State private var output: String?
    @State private var isRunning = false

    private func schema(for skill: RegisteredSkill) -> String {
        skill.inputSchema
            .map { "\($0.key): \($0.value)" }
            .sorted()
            .joined(separator: "\n")
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                WorkspaceHeader(
                    eyebrow: "LOCAL CAPABILITIES",
                    title: "Skills",
                    subtitle: "Inspectable, zero-token tools. Registered skills are side-effect-free."
                )
                if viewModel.skills.isEmpty {
                    ContentUnavailableView("No skills available", systemImage: "wand.and.stars")
                        .frame(maxWidth: .infinity, minHeight: 180)
                } else {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 250), spacing: 12)], spacing: 12) {
                        ForEach(viewModel.skills) { skill in
                            VStack(alignment: .leading, spacing: 9) {
                                Label(skill.name, systemImage: skill.type == "analysis" ? "chart.bar.fill" : "wand.and.stars")
                                    .font(.headline)
                                    .foregroundStyle(.white)
                                Text(skill.description).font(.subheadline).foregroundStyle(.white.opacity(0.72))
                                Text(skill.sideEffectFree ? "READ / TRANSFORM ONLY" : "ACTION REQUIRES APPROVAL")
                                    .font(.caption2.weight(.bold)).tracking(0.7)
                                    .foregroundStyle(skill.sideEffectFree ? .mint : .orange)
                                Text(schema(for: skill))
                                    .font(.caption.monospaced())
                                    .foregroundStyle(.white.opacity(0.55))
                            }
                            .padding(16)
                            .frame(maxWidth: .infinity, minHeight: 160, alignment: .topLeading)
                            .background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 18))
                            .overlay(RoundedRectangle(cornerRadius: 18).stroke(.cyan.opacity(0.2)))
                        }
                    }
                }
                VStack(alignment: .leading, spacing: 12) {
                    Text("TRY TEXT CLEANUP").font(.caption.weight(.bold)).tracking(1.2).foregroundStyle(.cyan)
                    TextEditor(text: $input).frame(minHeight: 100).padding(8).background(.black.opacity(0.2), in: RoundedRectangle(cornerRadius: 12))
                    Button(isRunning ? "Cleaning…" : "Clean text", systemImage: "wand.and.stars") {
                        isRunning = true
                        Task {
                            output = await viewModel.runTextCleanup(input)
                            isRunning = false
                        }
                    }
                    .buttonStyle(.borderedProminent).tint(.cyan)
                    .disabled(isRunning || input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    if let output {
                        Text(output).textSelection(.enabled).padding(12).frame(maxWidth: .infinity, alignment: .leading)
                            .background(.mint.opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                    }
                }
                .padding(18)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 20))
            }
            .padding(24)
        }
        .foregroundStyle(.white)
        .background(HUDBackground())
        .navigationTitle("Skills")
    }
}

private struct SystemWorkspace: View {
    @ObservedObject var viewModel: ChatViewModel
    @Binding var showSettings: Bool

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                WorkspaceHeader(
                    eyebrow: "CONTROL PLANE",
                    title: "System status",
                    subtitle: "Live state from your private DAKSH service, refreshed automatically."
                ) {
                    Button("Connection settings", systemImage: "gearshape") { showSettings = true }
                        .buttonStyle(.bordered)
                }
                MetricRow(values: [
                    ("AI core", viewModel.isConnected ? "Ready" : "Offline", "cpu.fill", viewModel.isConnected ? .green : .orange),
                    ("Workers", "\(viewModel.brainStatus?.commander?.workers ?? 0)", "person.3.fill", .blue),
                    ("Memory", "\(viewModel.brainStatus?.knowledgeGraph?.totalDocuments ?? 0)", "brain.head.profile.fill", .mint),
                    ("Skills", "\(viewModel.brainStatus?.skillRouter?.totalSkills ?? 0)", "wand.and.stars", .purple),
                ])
                Text("Cloud fallback: \(viewModel.systemStatus?.cloudFallbackEnabled == true ? "enabled" : "disabled")")
                    .font(.subheadline.weight(.semibold))
                    .padding(16)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 18))
            }
            .padding(24)
        }
        .background(HUDBackground())
        .navigationTitle("System")
    }
}

private struct WorkspaceHeader<Action: View>: View {
    let eyebrow: String
    let title: String
    let subtitle: String
    @ViewBuilder let action: () -> Action

    init(eyebrow: String, title: String, subtitle: String, @ViewBuilder action: @escaping () -> Action = { EmptyView() }) {
        self.eyebrow = eyebrow; self.title = title; self.subtitle = subtitle; self.action = action
    }

    var body: some View {
        HStack(alignment: .top, spacing: 18) {
            VStack(alignment: .leading, spacing: 6) {
                Text(eyebrow).font(.caption.weight(.bold)).tracking(1.3).foregroundStyle(.cyan)
                Text(title).font(.system(size: 34, weight: .bold, design: .rounded)).foregroundStyle(.white)
                Text(subtitle).foregroundStyle(.white.opacity(0.7))
            }
            Spacer()
            action()
        }
    }
}

private struct MetricRow: View {
    let values: [(String, String, String, Color)]

    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 145), spacing: 12)], spacing: 12) {
            ForEach(values, id: \.0) { title, value, icon, color in
                StatusCard(title: title, value: value, icon: icon, color: color)
            }
        }
    }
}

private struct DocumentRow: View {
    let document: BrainDocument

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: "doc.text.fill").font(.title2).foregroundStyle(.mint)
            VStack(alignment: .leading, spacing: 4) {
                Text(document.title).font(.headline)
                Text(document.source).font(.caption).foregroundStyle(.secondary).lineLimit(1)
                Text("\(document.chunks) chunks · \(document.entities) entities · \(document.createdAt.formatted(date: .abbreviated, time: .shortened))")
                    .font(.caption2).foregroundStyle(.secondary)
            }
            Spacer()
        }
        .padding(15)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(.mint.opacity(0.2)))
    }
}

private struct HUDBackground: View {
    var body: some View {
        LinearGradient(
            colors: [Color(red: 0.02, green: 0.06, blue: 0.12), Color(red: 0.02, green: 0.12, blue: 0.18)],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
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
