# DAKSH native client

This is a single SwiftUI source tree for **iOS 17+** and **macOS 14+**. It connects only to a DAKSH web dashboard over a configurable HTTPS Tailnet URL; it contains no cloud-provider API keys or provider configuration.

## Run in Xcode

1. Open `native/DAKSH/Package.swift` in Xcode 15 or newer, then select the **DAKSH** executable scheme.
2. Select either a macOS destination or an iOS simulator/device and run.
3. Open **Endpoint Settings** (gear button) and enter the dashboard origin, for example `https://daksh.your-tailnet.ts.net`. The value is persisted locally using `@AppStorage`.

## Voice input

The microphone button uses Apple Speech Recognition and the device microphone
for push-to-talk transcription. Before running on a physical iPhone or Mac,
add these privacy usage descriptions to the app target's `Info.plist` in
Xcode:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>DAKSH uses the microphone for push-to-talk requests.</string>
<key>NSSpeechRecognitionUsageDescription</key>
<string>DAKSH transcribes push-to-talk requests on your device.</string>
```

Tap the microphone button to begin speaking and tap it again to stop. The
recognized text appears in the composer; review it and press Send to submit it
to the private DAKSH server.

The client uses these existing server routes:

- `GET /api/daksh/history?limit=50`
- `POST /api/daksh/interact` with `{"input":"…","type":"text"}`

“Clear conversation” removes messages only from the current app view because the current DAKSH API has no server-side deletion endpoint. Reloading history may show those server records again.

## Command-line validation

On macOS with Swift tools installed:

```sh
cd native/DAKSH
swift test
swift run DAKSH
```

An Xcode project is deliberately not checked in: Swift Package Manager is directly Xcode-openable and avoids generated project metadata while retaining a shared universal codebase.
