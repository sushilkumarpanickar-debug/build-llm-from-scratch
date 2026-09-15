# Public capability review — 15 September 2026

Reference review of official public repositories/documentation, not installation or a security audit. Decisions below are DAKSH-specific assessments. Preserve the working local service; adopt a component only for a measured gap, with a pinned source/license, bounded access and a test.

| Candidate/source | Useful contribution | Decision for DAKSH |
|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful workflows, durable execution and human-in-the-loop | Best architectural reference for resumable approval workflows. Current simple local protocol uses no new dependency; evaluate runtime migration when multi-step jobs need durable checkpoints. |
| [Microsoft Agent Framework](https://github.com/microsoft/agent-framework/tree/main/python/samples/02-agents/providers/ollama) | Agent workflows with native Ollama provider | Alternative orchestration runtime; avoid adding alongside LangGraph. Evaluate compatibility before selecting one. |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | Browser automation through structured page interactions | Strong candidate for a bounded coding/browser verification worker, not yet connected to DAKSH. Logged-in actions need separate approvals. |
| [browser-use](https://github.com/browser-use/browser-use) | Agent browser tasks | Compare against Playwright MCP for dynamic web jobs; model reliability and browser permissions need testing. No hosted/default provider adopted. |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Native local speech inference | Benchmark on this Mac against working faster-whisper before replacing it; wake-word/VAD conversation is a separate gap. |
| [OpenHands](https://github.com/OpenHands/docs/blob/main/openhands/usage/llms/local-llms.mdx) | Local-model coding agent and isolated execution architecture | Optional future coding worker; Docker/model resource and access requirements need measurement. Not the core personal assistant. |
| [Open Interpreter](https://github.com/OpenInterpreter/open-interpreter/blob/main/docs/guides/running-locally.mdx) | Local models and computer/code execution patterns | Reference for narrow execution workflows; unrestricted code execution is not enabled. Distinguish this repository from similarly named newer projects. |
| [Mem0](https://github.com/mem0ai/mem0) | Retrieval/memory infrastructure | Reference only: DAKSH already owns scoped SQLite/RAG. Do not create a second authority or use managed memory benchmark scores as local guarantees. |
| [Open WebUI](https://github.com/open-webui/open-webui) | Mature local Ollama interaction patterns | UI reference, not a replacement for DAKSH's graph/native wrapper. Review current branding/license conditions before copying code. |
| [Marker](https://github.com/datalab-to/marker) | Rich PDF-to-Markdown/JSON conversion | Candidate only for scanned/layout-heavy documents that existing extraction fails. Review code/model licensing and Mac resource use before adoption. |

## JARVIS video check
[Zubair's video](https://www.youtube.com/watch?v=mitzci4FsOg) is titled “Is GPT-6 Astra Actually AGI? I Tested It Inside My JARVIS”. The creator's description links the finished installation to AI Workshop and a free prompt pack to AI Workshop Lite; it does not identify a public source repository for the finished build. Description/chapter review completed; transcript export returned unavailable and full media playback was unavailable. No claim of a frame-by-frame UI review is made.

The description separates model from mechanics: notes/chat/vision use the stated model, while tools, focus lock, camera and Telegram are application mechanics. DAKSH keeps Ollama instead of adopting that provider. Public brain-map and HOLO components already adopted are not proof that the full members' JARVIS implementation is public.

| Video capability | DAKSH state / gap |
|---|---|
| Second brain graph | Working public 2D graph adaptation; not the members-only 3D interface. |
| Voice and wake word | Local transcription/TTS and continuous voice exist; true live conversation acceptance and dedicated wake-word/VAD refinement remain. |
| Voice file search | Scoped document RAG exists; arbitrary whole-Mac file discovery is not enabled. |
| Live web research | Candidate tools reviewed; DAKSH chat has no automatic live browser/research worker. |
| Camera eyes / screen understanding | HOLO hand gestures are local note control, not general camera vision or screen observation. |
| Focus lock | Not implemented. Needs explicit application-observation scope and opt-in controls. |
| Telegram / Gmail / Calendar | Existing allowlisted instruction intake, approved Gmail drafts and read-only agenda; production account limits still apply. |
| Invoice automation | Finance/workflow drafts exist; validated invoice-generation business module is separate work. |

## Adoption sequence
1. Use the universal protocol now: shared task contracts, explicit routing, evidence and verification.
2. Finish real voice/camera acceptance before replacing engines.
3. Add one bounded browser worker with observable receipts and approval handling.
4. Add resumable execution/checkpoints only when actual multi-step workflows justify a runtime dependency.
5. Add opt-in local vision/focus controls and validated business document modules as separate implementations.

No new third-party installer, hosted inference, account permission, broad terminal access or automatic external action was enabled by this review.
