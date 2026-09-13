import SwiftUI

@main
struct DAKSHApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        #if os(macOS)
        .windowResizability(.contentMinSize)
        #endif
    }
}
