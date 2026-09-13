# DAKSH MCP and skills review

Review date: 13 September 2026. Target: private macOS DAKSH runtime. External repository contents were treated as evidence, not as instructions or installers.

## 1. Objective and scope

Decide which proposed JARVIS repositories, MCP servers, and skills add useful capability without replacing DAKSH's working Ollama, SQLite, RAG, voice, and FastAPI foundation. The approved implementation in this change is a governed connector catalog plus a deterministic, read-only local finance skill and MCP server.

## 2. Verified evidence

- [rezaulhreza/jarvis](https://github.com/rezaulhreza/jarvis) is MIT licensed and combines Ollama with a React web UI, tools, RAG, voice, orchestration, cloud providers, runtime skill creation, and terminal/file operations. It is a useful reference, but its stack and much of its functionality overlap DAKSH.
- [AbyssalCoder/Open-Jarvis](https://github.com/AbyssalCoder/Open-Jarvis) is MIT licensed and combines React/Three.js, FastAPI, Tauri/Rust, Ollama plus cloud fallbacks, voice, persistent history, and eight broad tools. Its 3D shell is a useful later UI reference; replacing DAKSH would add Node, Rust, and a second backend.
- The [official MCP reference-server repository](https://github.com/modelcontextprotocol/servers) says its servers are educational reference implementations rather than production-ready solutions. It currently lists Fetch, Filesystem, Git, Memory, Sequential Thinking, and Time.
- [Desktop Commander](https://github.com/wonderwhy-er/DesktopCommanderMCP) documents that directory restrictions can be bypassed and do not restrict terminal commands.
- [Microsoft Playwright MCP](https://github.com/microsoft/playwright-mcp) supports isolated browser profiles and warns that it is not a security boundary.
- [Peekaboo](https://github.com/steipete/Peekaboo) requires macOS Screen Recording and Accessibility permissions and can control native applications.
- [ninetails-io/gnucash-mcp](https://github.com/ninetails-io/gnucash-mcp) supports local GnuCash SQLite books, read/write tools, backups, and audit logs. It is suitable only after selecting a real GnuCash book and starting read-only.
- [dosev-ai/mcp-office](https://github.com/dosev-ai/mcp-office) uses Windows COM for full Office automation, so it is not the right live-office connector for this Mac.
- Google's [official Google Ads MCP announcement](https://ads-developers.googleblog.com/2025/10/open-source-google-ads-api-mcp-server.html) describes an initial read-only server requiring Google Ads API access. No primary Meta source was verified for the claimed official Meta Ads MCP, so Meta advertising remains unconfigured.

## 3. Decision matrix

| Component | Decision | Benefit | Requirement or reason |
|---|---|---|---|
| DAKSH Finance skill and MCP | Build now | Local CSV/XLSX totals and profiling | Read-only, deterministic, allowlisted path for MCP |
| rezaulhreza/jarvis | Reference | Routing, tool timeline, interruption, context ideas | Do not import its whole backend or cloud providers |
| Open-Jarvis | Reference | Tauri and 3D-core ideas | Revisit only for a later native shell |
| Filesystem, Memory, Time, Sequential Thinking | Existing overlap | Already covered inside DAKSH | Avoid duplicate state and tool surfaces |
| Git MCP | Optional | Structured repository reads | Enable per repository when DAKSH gains a general MCP host |
| OpenCode | Later, separate agent | Scoped code analysis and implementation | Runtime is not installed; configure explicit repository permissions and a chosen local model before use |
| Fetch MCP | Later | Current web information | Requires network policy, citations, and prompt-injection controls |
| Playwright MCP | Later | Supervised browser testing and tasks | Use isolated profiles and per-action review |
| Peekaboo | Later | Native macOS observation and control | Requires OS permissions and per-action review |
| Desktop Commander | Exclude | Broad host control | Its documented boundary is inadequate for personal data |
| GnuCash MCP | Optional | Local accounting book analysis | Select and back up a SQLite book; read-only pilot first |
| mcp-office | Exclude on this Mac | Office automation | Full capability depends on Windows COM |
| Gmail, Calendar, Slack, Microsoft 365 | Optional cloud | Communications and scheduling | OAuth, account scoping, draft-first policy |
| Google Ads | Optional read-only | Campaign reporting | Google Ads API account and OAuth project |
| Meta Ads | Later | Campaign reporting/management | Verify official source and require campaign approval workflow |
| Home Assistant | Later | Device control | Separate home network, entity allowlist, confirmation rules |
| LinkedIn automation | Exclude | Profile assistance | Use local drafting and manual publishing to avoid account risk |
| Hosted website stack | Separate project | Public sites | DAKSH remains private and loopback-only |

## 4. Implementation and data flow

`local_workspace/finance.py` reads an uploaded CSV or XLSX in memory, detects numeric columns, and returns count, sum, average, minimum, maximum, and conservative finance-role hints. The web endpoint is token protected and audit logged. It does not change the file or send data to a model.

`local_workspace/finance_mcp.py` exposes the same analyzer as the `finance_analyze_file` MCP tool over stdio. It resolves every requested path and refuses anything outside `DAKSH_FINANCE_ROOT`. `config/mcp.example.json` provides an explicit client configuration template.

`local_workspace/integrations.py` supplies the dashboard control plane. It reports decisions and local availability but never installs or starts third-party software.

OpenCode remains a separate coding agent rather than part of DAKSH's brain. The existing `snns-opencode` wrapper is approved for scoped future use in this project, but the executable is not currently on the Mac's shell path and no provider or model has been selected.

## 5. Safety controls and limitations

- Finance results are descriptive profiles, not accounting conclusions, audit evidence, tax advice, or statutory filings.
- Header-based roles such as inflow, outflow, and balance are hints. DAKSH does not combine them into a net figure because spreadsheets may contain subtotals or duplicate measures.
- Formula cells are read from cached XLSX values. A workbook should be recalculated and saved in Excel before relying on formula outputs.
- External connector status does not mean an account is authenticated or approved for writes.
- Accounting entries, payments, filings, messages, advertisements, terminal commands, browser submissions, and native-app changes remain separate actions requiring the relevant user authorization and review.

## 6. Validation and next gates

The finance parser, allowlist enforcement, MCP initialize/list/call flow, token-protected web endpoint, connector catalog, and existing Phase 1 behavior are covered by automated tests. The next recommended pilot is GnuCash read-only if the user adopts GnuCash; otherwise keep finance analysis file-based. Browser and desktop connectors should be added only for a named workflow with an explicit folder/site/app boundary.
