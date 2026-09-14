# DAKSH Phase 1 local workspace

DAKSH is a private second brain that runs on this Mac. Its JARVIS-style command centre uses the SNNS identity while every AI operation stays local: Qwen through Ollama, `nomic-embed-text` for document retrieval, `faster-whisper` for microphone transcription, macOS `say` for spoken replies, and SQLite for durable memory.

## One-time setup

```sh
./setup_mac.sh
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

`qwen3:8b` is the preferred model. DAKSH automatically falls back to another installed local chat model, including `qwen2.5:3b` on smaller Macs. The setup script never configures a paid API.

## Start

```sh
.venv/bin/python -m local_workspace.server
```

Open <http://127.0.0.1:9001>. The server deliberately binds only to the loopback interface. Use `--port 9003` if port 9001 is occupied.

## Phase 1 abilities

- Separate Personal, CA Professional, Tiwarta CFO, and SNNS Smartact domains.
- Multiple persistent conversations with local Qwen chat.
- Explicit categorized memory and “remember that…” capture.
- Local semantic RAG over PDF, TXT, Markdown, DOCX, CSV, and XLSX files.
- Source chips and filename/page/sheet citations in retrieved answers.
- Continuous conversational voice sessions: speak, pause, receive a short spoken reply, then continue talking.
- Local faster-whisper transcription, voice activity detection, and interruptible browser/macOS speech.
- Local mission planning and status tracking.
- Live health matrix for inference, embeddings, voice, speech, database, and network boundary.
- A command-center dashboard with AI core status, live intelligence, active local agents, mission timeline, system monitor, memory insights, model status, quick commands, and a persistent voice dock.
- Deterministic read-only finance profiling for CSV/XLSX files, plus a local stdio MCP tool constrained to an approved finance folder.
- A connector control plane that distinguishes built-in, optional, later, overlapping, and excluded integrations without auto-installing them.
- A repository-scoped Codebase Memory MCP connection for structural lookup with a persistent local cache.
- A unified Communications screen for Telegram instructions and approvals, local Gmail reply proposals with approved Gmail Draft creation, read-only Google Calendar imports, and signed WhatsApp Cloud API intake.

Runtime data is saved under `local_workspace/data/` and excluded from Git. The SQLite database is not encrypted; rely on macOS account and disk encryption for device-level protection. Domain separation is contextual inside a single-user application, not user authentication.

## Document learning

Upload a file from **Knowledge Base**. DAKSH extracts page or sheet text, splits it into overlapping chunks, creates embeddings through local Ollama, and saves the vectors in SQLite. Chat retrieves the most relevant chunks from the active domain and exposes their sources with the answer. This teaches DAKSH your material without retraining or changing the base model.

## Voice

Use **Start Voice Session** in the command dock, sidebar, or quick commands to open the full-screen DAKSH Voice Link. It listens until you pause, transcribes the turn locally with faster-whisper, sends it automatically to the local Ollama model, speaks DAKSH's concise answer, and resumes listening. **Interrupt / Listen** stops speech and opens the microphone for the next turn; **End Session** closes the microphone and speech engine. The smaller microphone inside normal Chat remains available for one-turn dictation and review before sending.

The first transcription downloads the selected open Whisper model to the local Hugging Face cache. `tiny` is the default for speed. Browser microphone permission is required. Voice sessions use an installed local browser or macOS voice and do not call a paid speech API.

## Validation

```sh
.venv/bin/python -m unittest local_workspace.test_server
```

Tests use temporary databases and mocked model output. Live validation additionally checks the installed Ollama chat model, embeddings, one document-grounded answer, a faster-whisper transcription, and the macOS speech command.

## Local finance MCP

Copy `config/mcp.example.json` into the configuration area of an MCP-compatible client and replace `DAKSH_FINANCE_ROOT` with one folder that DAKSH may read. The server exposes only `finance_analyze_file`; it accepts CSV/XLSX, refuses paths outside that folder, and never edits the source. See `MCP_AND_SKILLS_REVIEW.md` for the connector decisions and boundaries.

## Communications

Open **Messages** or **Calendar** in the left navigation to reach the unified Communications screen. The **Check Now** control polls configured Telegram, Gmail, and Google Calendar connections. WhatsApp uses a signed webhook instead of polling. Connector credentials are intentionally absent from Git; follow `COMMUNICATION_CONNECTORS.md` to connect your accounts locally.

New Gmail messages receive a local Ollama reply proposal in the approval queue. You can edit it in DAKSH; approval saves it as a threaded Gmail draft and Telegram can notify you with the approval number. DAKSH has no email-send operation. Telegram, WhatsApp, and specially marked Gmail instructions use a separate approval that stages a local mission without executing it automatically.

## Safety boundary

Document content is treated as untrusted reference data. DAKSH does not expose arbitrary shell execution or desktop automation. It refuses to persist common secret types as memory. Destructive conversation and document removal actions require an in-app confirmation and are written to the local audit log.

## Token-efficient routing

DAKSH uses Ollama first for private chat, RAG, and routine reasoning, so those turns have no metered API-token charge. Code questions can use the pinned Codebase Memory MCP through `.codex/config.toml`; its graph cache stays under ignored `local_workspace/data/` and the server exposes the restricted `analysis` tool profile. The wrapper refuses to run if the reviewed v0.10.8 binary is missing and supports an explicit `DAKSH_CBM_BINARY` override.

OpenCode remains a separate optional coding client. Its Zen free offers can change and are hosted, so DAKSH does not silently route personal context to them. Parallel Search is listed as an optional two-tool public-web service; it is not enabled because queries and fetched URLs are sent to Parallel. DAKSH's existing SQLite memory and document RAG remain authoritative, avoiding duplicate graph/RAG memory servers and conflicting writes.
