"""Governed DAKSH connector catalog. Catalog entries never auto-install software."""
from __future__ import annotations

import shutil


CATALOG = (
    {"id": "daksh-finance", "name": "DAKSH Finance MCP", "decision": "built_now", "access": "read-only", "cost": "free", "description": "Allowlisted local CSV/XLSX profiling with deterministic totals.", "available": lambda: True},
    {"id": "gnucash", "name": "GnuCash MCP", "decision": "optional", "access": "read-only first", "cost": "free", "description": "Useful only after a SQLite-format GnuCash book is selected and backed up.", "available": lambda: bool(shutil.which("gnucash"))},
    {"id": "git", "name": "Git MCP", "decision": "optional", "access": "repository scoped", "cost": "free", "description": "Useful for repo diffs and history; DAKSH already has project Git workflows.", "available": lambda: bool(shutil.which("git"))},
    {"id": "opencode", "name": "OpenCode", "decision": "later", "access": "repository scoped", "cost": "model dependent", "description": "Keep as a separate coding agent for approved repositories; no runtime is installed on this Mac.", "available": lambda: bool(shutil.which("opencode"))},
    {"id": "playwright", "name": "Playwright MCP", "decision": "later", "access": "isolated browser", "cost": "free", "description": "Add for supervised website testing; authenticated actions require review.", "available": lambda: bool(shutil.which("npx"))},
    {"id": "peekaboo", "name": "Peekaboo", "decision": "later", "access": "macOS UI", "cost": "free", "description": "Add only with Screen Recording and Accessibility permissions plus action approvals.", "available": lambda: bool(shutil.which("peekaboo"))},
    {"id": "filesystem", "name": "Filesystem MCP", "decision": "overlap", "access": "allowlisted", "cost": "free", "description": "DAKSH already provides scoped upload, indexing, retrieval, and deletion.", "available": lambda: False},
    {"id": "memory", "name": "Memory MCP", "decision": "overlap", "access": "local", "cost": "free", "description": "DAKSH already has domain-scoped SQLite memory and explicit capture.", "available": lambda: False},
    {"id": "desktop-commander", "name": "Desktop Commander", "decision": "excluded", "access": "host terminal", "cost": "free", "description": "Excluded because terminal access is broader than its directory restrictions.", "available": lambda: False},
    {"id": "office", "name": "mcp-office", "decision": "excluded", "access": "Office files", "cost": "free", "description": "The reviewed implementation requires Windows for COM automation; this target is macOS.", "available": lambda: False},
    {"id": "google-ads", "name": "Google Ads MCP", "decision": "later", "access": "read-only account", "cost": "API account", "description": "Useful when a Google Ads account and OAuth project are intentionally connected.", "available": lambda: False},
    {"id": "meta-ads", "name": "Meta Ads connector", "decision": "later", "access": "account read/write", "cost": "API account", "description": "Keep disabled until an official connector, credentials, and campaign approval workflow are selected.", "available": lambda: False},
)


def catalog():
    return [{**{key: value for key, value in item.items() if key != "available"}, "installed": bool(item["available"]())} for item in CATALOG]
