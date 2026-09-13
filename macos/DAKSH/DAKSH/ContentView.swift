import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var runtime: DAKSHRuntime

    var body: some View {
        VStack(spacing: 0) {
            header

            ZStack {
                if runtime.ready {
                    DAKSHWebView(url: DAKSHRuntime.localURL, reloadID: runtime.reloadID)
                        .background(Color.black)
                } else {
                    startupPanel
                }
            }
        }
        .background(Color(red: 0.01, green: 0.04, blue: 0.07))
    }

    private var header: some View {
        HStack(spacing: 12) {
            Image(nsImage: runtime.appIcon)
                .resizable()
                .scaledToFit()
                .frame(width: 34, height: 34)
                .shadow(color: .cyan.opacity(0.7), radius: 6)

            VStack(alignment: .leading, spacing: 2) {
                Text("DAKSH")
                    .font(.system(size: 15, weight: .semibold, design: .rounded))
                    .tracking(5)
                Text(runtime.statusLine)
                    .font(.system(size: 11, weight: .medium, design: .monospaced))
                    .foregroundStyle(runtime.statusColor)
                    .lineLimit(1)
            }

            Spacer()

            Button {
                runtime.chooseRepository()
            } label: {
                Image(systemName: "folder")
            }
            .help("Choose Repository")

            Button {
                runtime.syncAndRestart()
            } label: {
                Image(systemName: "arrow.triangle.2.circlepath")
            }
            .help("Sync From GitHub")

            Button {
                runtime.restartServerOnly()
            } label: {
                Image(systemName: "power")
            }
            .help("Restart Local Server")
        }
        .padding(.horizontal, 14)
        .frame(height: 56)
        .foregroundStyle(.white)
        .background(
            LinearGradient(
                colors: [
                    Color(red: 0.03, green: 0.14, blue: 0.20),
                    Color(red: 0.01, green: 0.05, blue: 0.08)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
    }

    private var startupPanel: some View {
        VStack(spacing: 18) {
            Image(nsImage: runtime.appIcon)
                .resizable()
                .scaledToFit()
                .frame(width: 124, height: 124)
                .shadow(color: .cyan.opacity(0.9), radius: 24)

            Text("DAKSH is starting")
                .font(.system(size: 24, weight: .semibold, design: .rounded))
                .tracking(2)

            Text(runtime.detailLine)
                .font(.system(size: 13, weight: .regular, design: .monospaced))
                .foregroundStyle(.white.opacity(0.72))
                .multilineTextAlignment(.center)
                .frame(maxWidth: 640)

            if runtime.needsSetup {
                Button("Run Local Setup") {
                    runtime.runSetup()
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(40)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .foregroundStyle(.white)
    }
}
