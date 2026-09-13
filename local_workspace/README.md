# DAKSH private workspace

A local working interface for the second-brain project. Uses Python's standard library and a locally installed Ollama model; no Python packages are required for this entry point.

## Start on your Mac

From the repository root:

```sh
python3 local_workspace/server.py
```

Open http://127.0.0.1:9001. Keep the terminal running. Ollama must be running with a downloaded local model for conversation and task planning. The UI discovers available models; it does not download models automatically. Notes work without a model. Use `--port 9003` if the default port is occupied.

## Implemented

- Responsive JARVIS-inspired command-centre interface using the supplied SNNS peacock identity, without external visual assets.
- Conversation, memory vault, mission control and systems matrix views.
- Persistent notes with title, source and creation date.
- Separate Personal, CA Professional, Tiwarta CFO and SNNS Smartact context.
- Local model responses with recent conversation context and keyword-matched notes.
- Model-generated task plans with user-managed status.
- Explicit readiness states, bounded requests, loopback binding and same-origin write token.
- No external scripts, fonts, analytics, cloud APIs or browser-storage copies of notes.

Data lives in `local_workspace/data/workspace.sqlite3`, excluded from Git. Back up that directory separately. The database is not encrypted by this application. Workspace separation is organisational, not authentication. This is a single-user, loopback-only development application, not a remotely deployable server.

## Boundaries

The legacy `daksh.web_dashboard` imports an absent `orchestrator.manager` module. This entry point is deliberately independent so that the new workspace runs without claiming the legacy orchestrator has been repaired. Existing source is preserved.

Task plans do not execute tools. Status changes are manual. There is no background scheduling, native voice capture, file parsing, OAuth, semantic vector search, autonomous agent execution or cloud provider connection yet. Notes use keyword-overlap retrieval, not semantic RAG. Responses are non-streaming and limited to 700 output tokens; at most one generation runs at once. The UI displays the most recent 200 records of each kind per scope; older records remain stored. A request may take up to two minutes on a slower model.

## Validation

```sh
python3 local_workspace/test_server.py
```

Tests cover branded asset delivery, persistence, workspace isolation, write/host protection, chat/task lifecycle, unavailable providers and cloud-model exclusion. Live local-model tests use synthetic data in a temporary database. No personal source material is committed.
