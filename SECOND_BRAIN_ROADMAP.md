# DAKSH: second-brain application structure

Research and source inspection: 13 September 2026. Baseline: `9f8576ac61d00fe57fda0a76f79554a583f6b393`.

## 1. Intended outcome

A personal workspace that remembers reference material and decisions, understands an objective, creates a plan, invokes bounded tools, produces reviewable artifacts, and records what actually happened. The application should combine existing language models with memory and tools. Training a foundation model from scratch is a separate undertaking and is not required to deliver this product.

## 2. Application structure

| Surface | User purpose | First implementation | Next milestone |
|---|---|---|---|
| Conversation | Think, ask and draft | Local Ollama chat; recent history; note references | Streaming, attachments, conversation threads |
| Knowledge | Capture and retrieve context | Persistent notes, provenance, keyword retrieval, workspace scope | PDF/DOCX ingestion, chunking, hybrid search, correction and archival |
| Tasks & agents | Turn objectives into work | AI plans and manual progress | Durable task state, checkpoints, tool invocation, retries, cancellation |
| Connections | Know available abilities | Local-model discovery and honest readiness | OAuth per service, MCP clients, narrowly scoped credentials |
| Review & artifacts | Check outputs before consequential actions | Planned | Artifact viewer, action proposals, approval and audit trail |
| Voice | Converse hands-free | Planned | Opt-in local STT/TTS, interruption handling, visible microphone state |
| Automations | Revisit recurring work | Planned | Local scheduler, missed-run recovery, actionable notifications |

## 3. Current repository findings

- `orchestrator/commander.py` imports `orchestrator.manager`, but that module is absent in the checked-out tree. The legacy UI imports this chain during startup.
- Flask defaults to looking for templates relative to its application package; the existing dashboard does not explicitly point to the root `templates` directory.
- The voice endpoint is a placeholder; it returns a processing label without decoding/transcribing audio.
- Conversation history/context in `daksh/interface.py` are in-memory and disappear on restart.
- The intent parser checks substrings such as `do`, which can misroute ordinary text containing those letters.
- The existing UI/backend uses fixed confidence and zero-token/unlimited-credit language. Local deterministic skills can avoid model calls; general reasoning still requires inference. Costs, usage and successful execution need measured evidence.
- Dependency/runtime compatibility for the legacy application has not been verified. Do not install the full old requirements file as the new workspace prerequisite.

The new `local_workspace` entry point provides a functioning foundation while leaving legacy modules intact. It does not assert that the old Commander/Manager/Worker runtime works.

The interface now uses the owner's SNNS peacock logo as the DAKSH system core. Its visual language borrows the useful traits of fictional HUDs—high contrast, concentric status rings, clear telemetry and spatial grouping—without copying third-party artwork or implying fictional capabilities.

The authenticated GitHub account currently exposes six owned repositories: `build-llm-from-scratch`, `codebase-memory-mcp`, `aegis-mvp`, `snns-smartact-platform`, `compliance-platform`, and `design-spark-forge-81`. They are recorded in the systems matrix as candidates, not live runtime integrations.

## 4. Repository research and reuse decisions

These are upstream project descriptions and architectural candidates, not security or performance certifications. No external repository code was copied or installed. Verify the exact release, licence, dependency tree, macOS requirements and behaviour before adoption.

| Project | Relevant capability | Proposed role | Limits / integration cost |
|---|---|---|---|
| [OpenJarvis](https://github.com/open-jarvis/OpenJarvis) | Local-first personal agents, tools and evaluation | Architecture reference; evaluate its execution layer in an isolated trial | Broad framework; avoid installing a second overlapping full application without a fit test |
| [PersonalJarvis](https://github.com/PersonalJarvis/PersonalJarvis) | Voice, dictation and desktop operation | Evaluate voice interaction and permission design | OS-specific automation and microphone requirements need Mac validation |
| [Khoj](https://github.com/khoj-ai/khoj) | Second-brain search, agents and automation | Reference for knowledge UX; consider a separate retrieval service | Overlaps much of DAKSH; review licence obligations before code reuse or redistribution |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful agent execution and human intervention | Candidate for durable task execution | Adds framework/checkpoint dependencies; does not supply trustworthy tools automatically |
| [Ollama](https://github.com/ollama/ollama) | Local model service | Used through local HTTP API in this implementation | Model ability, memory and latency vary; each model has its own licence |

API references: [chat](https://docs.ollama.com/api/chat), [model discovery](https://docs.ollama.com/api/tags).

Recommendation: retain DAKSH as the product, use the existing local Ollama installation for the first working version, then evaluate ONE durable orchestration framework. Treat J.A.R.V.I.S. repositories as capability references rather than combining several complete assistants. This reduces competing memory stores, configuration systems and permission models.

## 5. Build sequence and acceptance criteria

1. **Local workspace — implemented:** start without the broken legacy imports; save notes and history across restart; keep workspaces separate; generate real local-model replies and plans; show unavailable capabilities accurately.
2. **Knowledge ingestion:** selected files only, source/page citations, deduplication, retrieval evaluation, edit/archive/export and encrypted-backup design. Verify answers against a small curated corpus before importing business material.
3. **Reliable orchestration:** typed tool registry; durable states (queued/running/waiting/failed/completed); cancellation; replay protection; output artifact checks. Start with bounded read-only tools and document generation. Execution success comes from tool results, never the model's assertion.
4. **Connections and approvals:** integrate one service at a time, beginning with read-only email/calendar or selected folders. Verify sender/account identity, scopes and audit records. Save proposed external actions for review.
5. **Voice and desktop:** local speech recognition and synthesis, explicit listening indicator, push-to-talk first, then opt-in wake word. Test interruption and wrong-command recovery before computer control.
6. **Proactive assistance:** persistent scheduler and alerts, recovery after restart/sleep, quiet unchanged checks, spending/time budgets and observability.

Every major milestone should be validated, committed and pushed to GitHub under the owner's standing instruction. Do not publish private runtime data.

## 6. Verification and open decisions

Five automated local API tests pass: persistence/scope isolation, request protection, chat/task lifecycle, failure handling and cloud-model exclusion. Live Ollama verification uses synthetic notes and a temporary database. Browser visual/interaction testing has not been performed in this pass.

Still to decide before the corresponding integration: first real business workflow, documents to ingest, cloud-provider use if any, allowed computer actions, backup destination and preferred voice language. These choices do not block the local UI foundation.
