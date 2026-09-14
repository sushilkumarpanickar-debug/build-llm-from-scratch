import AppKit
import Foundation
import SwiftUI

@MainActor
final class DAKSHRuntime: ObservableObject {
    static let localURL = URL(string: "http://127.0.0.1:9001")!

    @Published var ready = false
    @Published var needsSetup = false
    @Published var statusLine = "Preparing local runtime"
    @Published var detailLine = "Checking repository, GitHub branch, virtual environment, and local server."
    @Published var reloadID = UUID()

    private let branch = "main"
    private let defaultRepositoryPath = "/Users/mayanagari/Documents/Codex/2026-09-13/mak/work/build-llm-from-scratch"
    private var repositoryPath: String
    private var serverProcess: Process?
    private var syncTimer: Timer?
    private var launchStarted = false

    init() {
        repositoryPath = UserDefaults.standard.string(forKey: "DAKSHRepositoryPath") ?? defaultRepositoryPath
    }

    var statusColor: Color {
        if ready { return .green }
        if needsSetup { return .orange }
        return .cyan
    }

    var appIcon: NSImage {
        if let image = NSImage(named: "AppIcon") {
            return image
        }
        let fallback = URL(fileURLWithPath: repositoryPath).appendingPathComponent("local_workspace/static/snns_emblem.png")
        return NSImage(contentsOf: fallback) ?? NSImage(size: NSSize(width: 64, height: 64))
    }

    func launch() {
        guard !launchStarted else { return }
        launchStarted = true
        syncAndRestart()
        syncTimer = Timer.scheduledTimer(withTimeInterval: 600, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.syncIfChanged() }
        }
    }

    func chooseRepository() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.directoryURL = URL(fileURLWithPath: repositoryPath)

        guard panel.runModal() == .OK, let url = panel.url else { return }
        repositoryPath = url.path
        UserDefaults.standard.set(repositoryPath, forKey: "DAKSHRepositoryPath")
        syncAndRestart()
    }

    func syncAndRestart() {
        Task {
            await updateFromGitHub()
            await restartServer()
        }
    }

    func restartServerOnly() {
        Task {
            await restartServer()
        }
    }

    func runSetup() {
        Task {
            let repo = URL(fileURLWithPath: repositoryPath)
            statusLine = "Running setup"
            detailLine = "Installing local Python dependencies from setup_mac.sh."
            let result = await Self.runProcess("/bin/zsh", ["setup_mac.sh"], in: repo)
            if result.exitCode == 0 {
                needsSetup = false
                await restartServer()
            } else {
                detailLine = result.combinedOutput.trimmedForDisplay(defaultValue: "Setup failed. Open the repository in Xcode or Terminal to inspect the script output.")
                statusLine = "Setup failed"
            }
        }
    }

    func stopServer() {
        serverProcess?.terminate()
        serverProcess = nil
    }

    private func syncIfChanged() {
        Task {
            let before = await currentHead()
            await updateFromGitHub()
            let after = await currentHead()
            if before != after {
                await restartServer()
            }
        }
    }

    private func updateFromGitHub() async {
        let repo = URL(fileURLWithPath: repositoryPath)
        guard FileManager.default.fileExists(atPath: repo.appendingPathComponent(".git").path) else {
            ready = false
            needsSetup = false
            statusLine = "Repository not found"
            detailLine = "Choose the build-llm-from-scratch folder to connect the Mac app to DAKSH."
            return
        }

        statusLine = "Syncing GitHub"
        detailLine = "Opening \(branch), then pulling the latest app and UI from GitHub."
        let fetch = await Self.runProcess("/usr/bin/git", ["fetch", "origin", branch], in: repo)
        if fetch.exitCode != 0 {
            statusLine = "GitHub fetch failed"
            detailLine = fetch.combinedOutput.trimmedForDisplay(defaultValue: "GitHub could not be reached. The app will try to use the local checkout.")
            return
        }

        let currentBranch = await Self.runProcess("/usr/bin/git", ["rev-parse", "--abbrev-ref", "HEAD"], in: repo)
        if currentBranch.stdout.trimmingCharacters(in: .whitespacesAndNewlines) != branch {
            let localBranch = await Self.runProcess("/usr/bin/git", ["show-ref", "--verify", "--quiet", "refs/heads/\(branch)"], in: repo)
            let switchResult: CommandResult
            if localBranch.exitCode == 0 {
                switchResult = await Self.runProcess("/usr/bin/git", ["switch", branch], in: repo)
            } else {
                switchResult = await Self.runProcess("/usr/bin/git", ["switch", "--track", "-c", branch, "origin/\(branch)"], in: repo)
            }
            if switchResult.exitCode != 0 {
                statusLine = "Branch switch skipped"
                detailLine = switchResult.combinedOutput.trimmedForDisplay(defaultValue: "The repository has local edits. Open the Git sidebar in Xcode or Terminal to review them.")
            }
        }

        let result = await Self.runProcess("/usr/bin/git", ["pull", "--ff-only", "origin", branch], in: repo)
        if result.exitCode != 0 {
            statusLine = "GitHub sync skipped"
            detailLine = result.combinedOutput.trimmedForDisplay(defaultValue: "The branch could not fast-forward. Local files may have edits that need review.")
        }
    }

    private func restartServer() async {
        let repo = URL(fileURLWithPath: repositoryPath)
        let python = repo.appendingPathComponent(".venv/bin/python")
        guard FileManager.default.isExecutableFile(atPath: python.path) else {
            ready = false
            needsSetup = true
            statusLine = "Setup needed"
            detailLine = ".venv/bin/python was not found. Run local setup from this window or from setup_mac.sh."
            return
        }

        ready = false
        needsSetup = false
        statusLine = "Starting server"
        detailLine = "Restarting the local DAKSH service on 127.0.0.1:9001."

        stopServer()
        _ = await Self.runProcess("/bin/zsh", ["-lc", "/usr/sbin/lsof -ti tcp:9001 | /usr/bin/xargs /bin/kill -TERM 2>/dev/null || true"], in: repo)

        do {
            let process = Process()
            process.currentDirectoryURL = repo
            process.executableURL = python
            process.arguments = ["-m", "local_workspace.server"]
            process.environment = Self.runtimeEnvironment(for: repo)

            let logURL = repo.appendingPathComponent("local_workspace/data/daksh-mac-app.log")
            try FileManager.default.createDirectory(at: logURL.deletingLastPathComponent(), withIntermediateDirectories: true)
            FileManager.default.createFile(atPath: logURL.path, contents: nil)
            let handle = try FileHandle(forWritingTo: logURL)
            handle.seekToEndOfFile()
            process.standardOutput = handle
            process.standardError = handle

            try process.run()
            serverProcess = process
        } catch {
            statusLine = "Server failed"
            detailLine = error.localizedDescription
            return
        }

        let ok = await waitForServer()
        if ok {
            ready = true
            statusLine = "Ready"
            detailLine = "DAKSH is running locally at \(Self.localURL.absoluteString)."
            reloadID = UUID()
        } else {
            statusLine = "Server not ready"
            detailLine = "The app started the server process, but /api/health did not respond yet. Check local_workspace/data/daksh-mac-app.log."
        }
    }

    private func waitForServer() async -> Bool {
        for _ in 0..<40 {
            do {
                let (_, response) = try await URLSession.shared.data(from: Self.localURL.appendingPathComponent("api/health"))
                if let http = response as? HTTPURLResponse, http.statusCode == 200 {
                    return true
                }
            } catch {
                try? await Task.sleep(nanoseconds: 300_000_000)
            }
        }
        return false
    }

    private func currentHead() async -> String {
        let repo = URL(fileURLWithPath: repositoryPath)
        let result = await Self.runProcess("/usr/bin/git", ["rev-parse", "HEAD"], in: repo)
        return result.stdout.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    nonisolated private static func runtimeEnvironment(for repo: URL) -> [String: String] {
        var env = ProcessInfo.processInfo.environment
        env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        env["PYTHONPATH"] = repo.path
        return env
    }

    nonisolated private static func runProcess(_ executable: String, _ arguments: [String], in directory: URL) async -> CommandResult {
        await Task.detached {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: executable)
            process.arguments = arguments
            process.currentDirectoryURL = directory
            process.environment = runtimeEnvironment(for: directory)

            let stdout = Pipe()
            let stderr = Pipe()
            process.standardOutput = stdout
            process.standardError = stderr

            do {
                try process.run()
                process.waitUntilExit()
                let out = String(data: stdout.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
                let err = String(data: stderr.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
                return CommandResult(exitCode: process.terminationStatus, stdout: out, stderr: err)
            } catch {
                return CommandResult(exitCode: 127, stdout: "", stderr: error.localizedDescription)
            }
        }.value
    }
}

struct CommandResult {
    let exitCode: Int32
    let stdout: String
    let stderr: String

    var combinedOutput: String {
        [stdout, stderr].filter { !$0.isEmpty }.joined(separator: "\n")
    }
}

private extension String {
    func trimmedForDisplay(defaultValue: String) -> String {
        let trimmed = trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return defaultValue }
        if trimmed.count <= 500 { return trimmed }
        let end = trimmed.index(trimmed.startIndex, offsetBy: 500)
        return String(trimmed[..<end])
    }
}
