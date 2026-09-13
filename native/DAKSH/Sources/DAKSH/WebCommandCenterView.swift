import SwiftUI
import WebKit

/// Hosts DAKSH's richer JARVIS-style command center (voice reactor core, live
/// task/finance/knowledge panels) which is served as a local web app by
/// `local_workspace/server.py`. The native shell simply wraps it in a WKWebView
/// so Mac and iPhone share one interface without duplicating it in SwiftUI.
struct WebCommandCenterView: View {
    @AppStorage("commandCenterBaseURL") private var baseURLString = "http://127.0.0.1:9001"
    @State private var reloadID = UUID()
    @State private var loadFailed = false
    @State private var isEditingURL = false
    @State private var draftURL = ""

    private var resolvedURL: URL? {
        URL(string: baseURLString)
    }

    var body: some View {
        ZStack {
            if let url = resolvedURL {
                DAKSHWebView(url: url, reloadID: reloadID, loadFailed: $loadFailed)
                    .id(reloadID)
            }

            if loadFailed {
                connectionErrorOverlay
            }
        }
        .toolbar {
            ToolbarItemGroup {
                Button {
                    reloadID = UUID()
                    loadFailed = false
                } label: {
                    Label("Reload", systemImage: "arrow.clockwise")
                }
                Button {
                    draftURL = baseURLString
                    isEditingURL = true
                } label: {
                    Label("Server URL", systemImage: "server.rack")
                }
            }
        }
        .sheet(isPresented: $isEditingURL) {
            urlEditor
        }
    }

    private var connectionErrorOverlay: some View {
        VStack(spacing: 14) {
            Image(systemName: "wifi.exclamationmark")
                .font(.system(size: 40))
                .foregroundStyle(.orange)
            Text("Can't reach the DAKSH command center")
                .font(.headline)
            Text("Start it with `python3 local_workspace/server.py` on your Mac, then confirm the address below is reachable from this device.")
                .font(.caption)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
                .frame(maxWidth: 360)
            Text(baseURLString)
                .font(.caption.monospaced())
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(.thinMaterial, in: Capsule())
            Button("Try Again") {
                reloadID = UUID()
                loadFailed = false
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(28)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20))
        .padding()
    }

    private var urlEditor: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Command Center Address")
                .font(.headline)
            Text("On this Mac use http://127.0.0.1:9001. On iPhone, use the HTTPS address from Tailscale Serve so the connection is encrypted off-device.")
                .font(.caption)
                .foregroundStyle(.secondary)
            TextField("http://127.0.0.1:9001", text: $draftURL)
                #if os(iOS)
                .textInputAutocapitalization(.never)
                .keyboardType(.URL)
                #endif
                .autocorrectionDisabled()
                .textFieldStyle(.roundedBorder)
            HStack {
                Spacer()
                Button("Cancel") { isEditingURL = false }
                Button("Save") {
                    baseURLString = draftURL
                    reloadID = UUID()
                    loadFailed = false
                    isEditingURL = false
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(24)
        .frame(minWidth: 360)
    }
}

#if os(macOS)
import AppKit

private struct DAKSHWebView: NSViewRepresentable {
    let url: URL
    let reloadID: UUID
    @Binding var loadFailed: Bool

    func makeCoordinator() -> Coordinator { Coordinator(loadFailed: $loadFailed) }

    func makeNSView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.mediaTypesRequiringUserActionForPlayback = []
        let view = WKWebView(frame: .zero, configuration: configuration)
        view.navigationDelegate = context.coordinator
        view.uiDelegate = context.coordinator
        view.setValue(false, forKey: "drawsBackground")
        view.load(URLRequest(url: url))
        return view
    }

    func updateNSView(_ nsView: WKWebView, context: Context) {
        nsView.load(URLRequest(url: url))
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate {
        let loadFailed: Binding<Bool>
        init(loadFailed: Binding<Bool>) { self.loadFailed = loadFailed }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            loadFailed.wrappedValue = false
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            loadFailed.wrappedValue = true
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            loadFailed.wrappedValue = true
        }

        @available(macOS 12.0, *)
        func webView(
            _ webView: WKWebView,
            requestMediaCapturePermissionFor origin: WKSecurityOrigin,
            initiatedByFrame frame: WKFrameInfo,
            type: WKMediaCaptureType,
            decisionHandler: @escaping (WKPermissionDecision) -> Void
        ) {
            let localOrigin = origin.host == "127.0.0.1" || origin.host == "localhost"
            decisionHandler(localOrigin ? .grant : .deny)
        }
    }
}
#else
import UIKit

private struct DAKSHWebView: UIViewRepresentable {
    let url: URL
    let reloadID: UUID
    @Binding var loadFailed: Bool

    func makeCoordinator() -> Coordinator { Coordinator(loadFailed: $loadFailed) }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        let view = WKWebView(frame: .zero, configuration: configuration)
        view.navigationDelegate = context.coordinator
        view.uiDelegate = context.coordinator
        view.load(URLRequest(url: url))
        return view
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {
        uiView.load(URLRequest(url: url))
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate {
        let loadFailed: Binding<Bool>
        init(loadFailed: Binding<Bool>) { self.loadFailed = loadFailed }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            loadFailed.wrappedValue = false
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            loadFailed.wrappedValue = true
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            loadFailed.wrappedValue = true
        }
    }
}
#endif
