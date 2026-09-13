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
