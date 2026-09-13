# v0.8.0 - Local OpenCode Development

- Added OpenCode as a pinned upstream submodule.
- Added a local Ollama-only coding-agent runner with repository-root
  enforcement, external-directory denial, and bounded job execution.
- Added secure DAKSH APIs for submitting and monitoring development jobs.

# v0.7.0 - Installable Native Apps

- Added source-controlled Xcode targets for native iOS and macOS DAKSH AI apps.
- Added signing-ready bundle identifiers, shared Xcode schemes, required voice
  permissions, and macOS sandbox entitlements.
- Added verified instructions for device signing and deployment with Xcode.

# v0.6.0 - DAKSH AI Command Center

- Redesigned the web dashboard and native client as responsive DAKSH AI command
  centers with an original local-AI visual system.
- Added live web status, memory, routing, agent, and task cards backed by the
  local dashboard APIs.
- Added browser dictation and optional speech playback to the web interface.

# v0.5.0 - Native Voice Input

- Added native push-to-talk transcription with Apple Speech Recognition.
- Added explicit microphone and speech-recognition permission handling.
- Kept voice requests local to the device until the user reviews and sends the
  recognized text to the private DAKSH service.

# v0.4.1 - Native Build Cleanup

- Removed generated Swift Package build artifacts from the native app release.

# v0.4.0 - Native DAKSH

- Added a shared SwiftUI native client for macOS and iOS.
- Added Tailnet endpoint configuration stored locally on each device.
- Added native conversation history, message sending, error display, and
  new-conversation controls.

# v0.3.0 - DAKSH Web App

- Rebuilt the dashboard as a responsive ChatGPT-style chat application for
  macOS and iPhone browsers.
- Added conversation-history restore, request validation, local-system status,
  and a new-conversation control.
- Added PWA metadata and an offline app shell for installable mobile access.
- Fixed Flask template and static-asset resolution for the repository layout.

# v0.2.0 - Local-First DAKSH

- Added a local-first Ollama routing policy with `qwen2.5:3b` as the default
  model for Apple Silicon Macs with 8 GB unified memory.
- Made cloud providers an explicit, disabled-by-default fallback so API
  credits cannot be consumed accidentally.
- Added iCloud Drive persistence for DAKSH interaction history.
- Documented private iPhone access through Tailscale Serve.
- Removed unrestricted dashboard CORS and its unused dependency.
- Restored the missing manager runtime component and configuration values
  required by the documented local orchestration path.
