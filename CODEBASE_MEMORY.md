# DAKSH Codebase Memory

- Validation date: 13 September 2026
- Canonical project: `DeusData/codebase-memory-mcp`
- Pinned binary: `0.10.8`, Apple Silicon
- Index name: `daksh-build-llm`
- Index mode: `fast`
- Tool profile: `analysis`
- Cache: `local_workspace/data/codebase-memory/` (Git ignored)
- Source state during initial index: HEAD `550479705b2aaf8d5f80cef1de96166f06771df7` with the current logo, connector, documentation, and MCP configuration changes uncommitted

The validated index reported 754 nodes and 2,270 edges with no partial parses. The explicit `.cbmignore` excludes Git data, virtual environments, runtime databases, model/cache directories, environment files, and Python caches. The graph query `open voice mode` located the local voice endpoints and `local_workspace.voice.transcribe`; the current source confirms that function in `local_workspace/voice.py`. This verifies structural discovery without treating the graph as authoritative over current source.

The project-local `.codex/config.toml` launches `scripts/codebase_memory_mcp.sh`. The wrapper uses the reviewed binary directly, avoids the client-modifying installer, fixes the working directory to this repository, and stores generated graph data outside Git. Set `DAKSH_CBM_BINARY` only when deliberately testing another reviewed binary.

The index contains code structure only. It is not a source of business facts, personal memory, accounting data, or statutory conclusions.
