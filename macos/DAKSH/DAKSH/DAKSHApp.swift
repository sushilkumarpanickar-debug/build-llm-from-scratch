import SwiftUI

@main
struct DAKSHApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var runtime = DAKSHRuntime()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(runtime)
                .frame(minWidth: 1100, minHeight: 720)
                .onAppear {
                    runtime.launch()
                    appDelegate.runtime = runtime
                }
        }
        .commands {
            CommandMenu("DAKSH") {
                Button("Sync From GitHub") {
                    runtime.syncAndRestart()
                }
                .keyboardShortcut("r", modifiers: [.command, .shift])

                Button("Restart Local Server") {
                    runtime.restartServerOnly()
                }
                .keyboardShortcut("r", modifiers: [.command])
            }
        }
    }
}

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    weak var runtime: DAKSHRuntime?

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    func applicationWillTerminate(_ notification: Notification) {
        runtime?.stopServer()
    }
}
