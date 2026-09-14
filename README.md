# DAKSH · SNNS Local Intelligence

DAKSH Phase 1 is a private local-first JARVIS-style second brain for macOS. It uses free local models through Ollama, local faster-whisper voice input, macOS speech output, SQLite memory, document learning/RAG for PDF, TXT, Markdown, DOCX, CSV, and XLSX, deterministic finance profiling, and an approval-controlled communications bridge.

The application runs on `127.0.0.1` by default. It does not require paid AI APIs, hosted inference, cloud analytics, or cloud storage.

## Run the local web app

```sh
./setup_mac.sh
ollama pull nomic-embed-text
.venv/bin/python -m local_workspace.server
```

Then open <http://127.0.0.1:9001>.

## Native Mac app for Xcode

Open `macos/DAKSH/DAKSH.xcodeproj` in Xcode, choose the `DAKSH` scheme, and press **Run**. If Xcode shows `.cbmignore` or other plain repository files, you opened the repository folder instead of the app project.

The Mac app syncs the GitHub branch, starts the local DAKSH server, and opens the JARVIS-style UI in a native WebKit window. It also checks GitHub every ten minutes while open and restarts the local server when the branch fast-forwards.

To build a packaged app from Terminal:

```sh
zsh scripts/build_macos_app.sh
```

That produces `dist/DAKSH.app` and `dist/DAKSH-macOS-app.zip`.

## What is included

- Local Ollama chat with source-aware RAG.
- Persistent SQLite conversation history and explicit scoped memory.
- Personal, CA Professional, Tiwarta CFO, and SNNS Smartact memory scopes.
- PDF, TXT, Markdown, DOCX, CSV, and XLSX ingestion.
- Continuous voice mode: browser microphone → faster-whisper → local LLM → macOS `say`.
- AI Agent Hub for ChatGPT-like conversation, Codex/OpenCode-like coding, Claude-like document work, Gemini-like multimodal planning, Perplexity-like sourced research, and supervised tool orchestration.
- JARVIS-style DAKSH command-center UI with the transparent SNNS peacock/phoenix emblem.
- Governed connector control plane with a read-only local Finance MCP.
- Unified Telegram, Gmail, Google Calendar, and WhatsApp connector screen with allowlists, read-only Google access, staged instructions, and human approvals.
- Codebase Memory MCP helper for token-efficient repository indexing.

## Project guides

- `local_workspace/README.md` — complete Phase 1 run guide.
- `macos/DAKSH/README.md` — Xcode and native app guide.
- `MCP_AND_SKILLS_REVIEW.md` — MCP/skill decisions and connector boundaries.
- `COMMUNICATION_CONNECTORS.md` — guided Telegram, Google, and WhatsApp setup.
- `CODEBASE_MEMORY.md` — local codebase-memory setup.
- `COMPLETE_README.md` and the older Python modules — preserved orchestration research for later phases.
