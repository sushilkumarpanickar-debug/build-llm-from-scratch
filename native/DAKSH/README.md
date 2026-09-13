# DAKSH native client

This is a single SwiftUI source tree for **iOS 17+** and **macOS 14+**. It connects only to a DAKSH web dashboard over a configurable HTTPS Tailnet URL; it contains no cloud-provider API keys or provider configuration.

## Build and deploy in Xcode

1. Open `native/DAKSH/DAKSH.xcodeproj` in Xcode 15 or newer.
2. Choose either the **DAKSH iOS** or **DAKSH macOS** scheme and select a
   simulator, connected device, or local Mac destination.
3. To deploy to hardware, connect and unlock the iPhone/iPad (tap **Trust**
   when prompted) or connect the Mac, then select that device from Xcode's
   run destination menu.
4. In the target's **Signing & Capabilities** tab, select your paid Apple
   Developer Team. Xcode creates the necessary provisioning profile. The
   checked-in project intentionally has no development team selected.
5. Press Run. On a first device launch, approve the microphone and speech
   recognition prompts. Open **Endpoint Settings** (gear button) and enter the
   dashboard origin, for example `https://daksh.your-tailnet.ts.net`. The value
   is persisted locally using `@AppStorage`.

The apps use distinct bundle identifiers:

- iOS: `com.dakshai.client.ios`
- macOS: `com.dakshai.client.macos`

Both targets compile the shared files in `Sources/DAKSH`, support iOS 17+ and
macOS 14+, and include the required microphone and speech-recognition privacy
descriptions. The macOS target is sandboxed with microphone and outbound
network access enabled.

## Voice input

The microphone button uses Apple Speech Recognition and the device microphone
for push-to-talk transcription. Both app targets already declare the necessary
privacy usage descriptions in `Configuration/`.

Tap the microphone button to begin speaking and tap it again to stop. The
recognized text appears in the composer; review it and press Send to submit it
to the private DAKSH server.

The client uses these existing server routes:

- `GET /api/daksh/history?limit=50`
- `POST /api/daksh/interact` with `{"input":"…","type":"text"}`

“Clear conversation” removes messages only from the current app view because the current DAKSH API has no server-side deletion endpoint. Reloading history may show those server records again.

## Command-line validation

The Swift Package remains available for its tests. On macOS with Xcode:

```sh
cd native/DAKSH
swift test
xcodebuild -project DAKSH.xcodeproj -scheme "DAKSH macOS" \
  -destination 'platform=macOS' CODE_SIGNING_ALLOWED=NO build
xcodebuild -project DAKSH.xcodeproj -scheme "DAKSH iOS" \
  -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build
```

Use the Xcode project—not `Package.swift`—to build installable applications.
