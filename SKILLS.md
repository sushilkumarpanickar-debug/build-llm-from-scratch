# Project skill decisions

The user authorized Phase 1 implementation and supplied the SNNS logo, JARVIS reference video, and local-only requirements on 13 September 2026.

| Skill | Purpose | Decision and boundary |
|---|---|---|
| Sites building | Structure and visually validate the responsive local interface | Approved for this repository; hosting is excluded because the app is private on this Mac. |
| PDF | Implement and verify local PDF text extraction | Approved for Phase 1 ingestion; source documents remain local and are not committed. |
| Documents | Implement DOCX text and table extraction | Approved for Phase 1 ingestion; no cloud document service. |
| Spreadsheets | Implement CSV/XLSX sheet extraction | Approved for Phase 1 ingestion; workbook files remain local and are not modified. |
| DAKSH Finance | Deterministic local profiling of finance CSV/XLSX files | Approved by the user's 13 September 2026 request to connect finance skills and MCP; read-only, audit logged, and no AI-generated figures. |
| DAKSH Finance MCP | Make the finance profiler available to compatible local MCP clients | Approved for this repository; stdio only, one read-only tool, and paths restricted to `DAKSH_FINANCE_ROOT`. |
| MCP control plane | Show reviewed connector decisions and actual local availability | Approved for this repository; it does not auto-install, authenticate, start, or grant access to third-party connectors. |
| External JARVIS repositories | Source architectural and UI ideas | Reference-only. Their installers, cloud providers, broad tools, and application stacks are not adopted. |
| External MCP servers | Add capability for named workflows | Not installed by this review. Each optional connector retains its stated scope and requirements in `MCP_AND_SKILLS_REVIEW.md`. |
| OpenCode | Use a separate coding agent for bounded work in this repository | Project use is approved through `snns-opencode`; runtime is not installed, and future execution must use an explicit model and repository scope with reviewed diffs. |

No paid AI provider skill or hosted inference is approved for this project.
