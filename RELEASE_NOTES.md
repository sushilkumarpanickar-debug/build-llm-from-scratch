# v0.16.0 - Command Center Web UI + Local Workspace Backend

- Brought in the more advanced JARVIS-style command center UI (holographic
  core, live voice card, Agents/Tasks/Finance/Knowledge Base/Workflows
  sidebar) as `local_workspace/` — a FastAPI backend + static UI that runs
  alongside the existing Flask dashboard.
- Fixed a Python 3.9 runtime incompatibility (`int | None` typed parameter)
  in `local_workspace/server.py` so it runs correctly on macOS's stock
  system Python, not only newer interpreters.
- Added `WebCommandCenterView` to the native macOS/iPhone app: a WKWebView
  wrapper that loads this richer command center as the app's new default
  landing section, with a reload control and an editable server-address
  sheet, while keeping the existing native Chat/Memory/Documents/Skills/
  System workspaces reachable from the sidebar.
- Added the same App Transport Security local-networking allowance and a new
  `NSLocalNetworkUsageDescription` to the iOS target's Info.plist so an
  iPhone can reach a Mac-hosted DAKSH server, mirroring the earlier macOS fix.
- Verified end-to-end via the local_workspace server's access log: the
  rebuilt native macOS app's WebView successfully requested `/`, `/app.js`,
  `/style.css`, and live `/api/state`/`/api/health` data.

# v0.15.1 - Native Local Connection Repair

- Added the macOS App Transport Security local-network allowance required for
  the native app to reach its explicitly permitted `127.0.0.1` DAKSH server.
- Replaced ambiguous “ready” status with live endpoint-specific connection
  feedback and surfaced failed status refreshes in the app.

# v0.15.0 - Native Command Cockpit

- Replaced the sparse native Chat page with a dense DAKSH command cockpit:
  compact active core, quick-command deck, live activity rail, real backend
  telemetry, persistent command dock, and responsive desktop/mobile layout.
- Added a dedicated animated voice console with explicit listen, transcript
  review, send, and local-device privacy states.
- Each quick command is connected to DAKSH's real local assistant and private
  memory rather than simulated interface activity.

# v0.14.2 - Native Dashboard Layout

- Made the DAKSH native app open as a dark, balanced, desktop-sized workspace
  rather than inheriting a small or sparse previous window layout.
- Preserved responsive navigation while ensuring the Chat, Memory, Documents,
  Skills, and System surfaces have a usable minimum presentation.

# v0.14.1 - Installed Native App and Icon Fix

- Corrected the macOS target resource phase so the DAKSH icon is included in
  the built application bundle and recognized by Finder and the Dock.
- Tightened the Chat workspace header so active conversation content and
  controls remain the focus on first launch.
- Installed the verified native build at `~/Applications/DAKSH AI.app`.

# v0.14.0 - Native Workspace Navigation

- Rebuilt the native DAKSH client from a single command-center screen into
  functional Chat, Memory, Documents, Skills, and System workspaces.
- Added selectable recent private requests, a source-traceable memory library,
  and a device-native document picker connected to the protected import API.
- Added an interactive local text-cleanup skill console and live service
  telemetry across the native interface.

# v0.13.0 - Native HUD and Local Document Ingestion

- Completed the reactive native second-brain HUD: macOS and iPhone clients now
  display live graph, skill, and worker telemetry and can save private notes.
- Added local dashboard document import for TXT, Markdown, CSV, JSON, DOCX,
  and text-based PDF files, with a 10 MB default limit and explicit failures
  for unsupported or unreadable documents.
- Added SHA-256 content deduplication and a discoverable, public skill registry
  for DAKSH’s side-effect-free text processing, data analysis, and synthesis.

# v0.12.0 - Interactive Second Brain HUD

- Rebuilt the web dashboard as a responsive, live DAKSH HUD with a central core,
  system telemetry, quick actions, command channel, and private-memory capture.
- Made the knowledge graph durable in the private DAKSH data directory and added
  documented memory/query APIs with source-traceable chat grounding.
- Registered built-in text processing, data analysis, and synthesis skills at
  runtime, and corrected natural-language command parsing.

# v0.11.0 - Durable Approved Actions

- Persisted approval-gated OpenCode jobs and their terminal results safely across
  dashboard restarts.
- Bound approvals to SHA-256 request fingerprints and recorded prompt-free audit
  events for job and approval transitions.
- Added the supplied transparent peacock logo to the native and web interfaces.

# v0.10.0 - Local Mac Connection

- Connected the macOS native app to the local DAKSH service automatically.
- Permitted HTTP only for loopback addresses on macOS while retaining HTTPS
  enforcement for remote and iPhone connections.

# v0.9.0 - Telegram Approval Gate

- Added Telegram approvals for OpenCode development jobs, bound to a single
  configured private chat.
- Added persistent, expiring approvals requiring exact `APPROVE <id>` or
  `DENY <id>` commands before a coding job can start.
- Verified the bundled local `qwen2.5:3b` model runs successfully with Ollama.

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
