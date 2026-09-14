# DAKSH Phase 1 status

Status reviewed: 14 September 2026.

## Completed in the application

- Private FastAPI service on `127.0.0.1` with health, chat, conversations, memory, documents, settings, voice, finance, tasks, connectors, and approvals.
- Local Ollama chat and embeddings, source-aware document RAG, persistent scoped SQLite storage, explicit memory, audit logging, and no paid AI requirement.
- PDF, TXT, Markdown, DOCX, CSV, and XLSX ingestion.
- Continuous faster-whisper voice conversation with macOS speech output.
- Responsive DAKSH/SNNS command-center UI and native SwiftUI/WebKit Xcode application.
- Telegram and WhatsApp instruction intake with allowlists and approvals.
- Gmail inbox import, complete text-body extraction, local Ollama reply proposals, editable approvals, approved Gmail Draft creation, and Telegram approval notifications.
- Read-only Google Calendar agenda import.
- Deterministic finance analysis and the allowlisted local Finance MCP.
- Automated tests, setup instructions, GitHub branch synchronization, and packaged Mac application.

## Remaining before Phase 1 is operational on the user's accounts

1. Create or select the Telegram bot and record its private token plus the user's allowed chat ID in the local `.env`.
2. Create the Google Desktop OAuth client, enable Gmail and Calendar APIs, run `scripts/setup_google_connectors.py`, and approve the Gmail read/compose and Calendar read-only scopes.
3. Test one real incoming email through proposal, Telegram/app approval, and Gmail Draft creation. Sending remains a manual Gmail action.
4. Choose a polling interval after the Telegram and Google credentials work. Polling remains off by default until then.
5. Either configure the optional Meta WhatsApp Cloud API, signed HTTPS webhook, and allowed numbers, or formally defer WhatsApp because Meta setup and possible message charges are outside the local/free core.
6. Perform the final user acceptance check in the Xcode app: microphone permission, one continuous voice conversation, one private document-grounded answer, and one approved email draft.
7. Merge the current GitHub pull request after reviewing the major connector implementation.

## Later-phase work

Email attachment-aware reply drafting, automatic sending, calendar editing, browser control, desktop control, statutory portal submissions, payments, and autonomous external actions are not Phase 1 capabilities. They require separate tool permissions, narrow workflows, and action-specific approvals.
