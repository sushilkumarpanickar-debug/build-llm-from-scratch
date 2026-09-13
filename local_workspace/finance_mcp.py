"""Minimal stdio MCP server exposing DAKSH's read-only finance profiler."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    from .finance import analyze_path
except ImportError:
    from finance import analyze_path

SERVER_INFO = {"name": "daksh-finance", "version": "1.0.0"}
TOOL = {
    "name": "finance_analyze_file",
    "description": "Read and deterministically profile a CSV or XLSX file inside DAKSH_FINANCE_ROOT. Does not modify the file.",
    "inputSchema": {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Absolute or root-relative path to a CSV/XLSX file."}},
        "required": ["path"],
        "additionalProperties": False,
    },
}


def handle(message, allowed_root):
    method = message.get("method")
    identifier = message.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": identifier, "result": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": identifier, "result": {"tools": [TOOL]}}
    if method == "tools/call":
        params = message.get("params") or {}
        if params.get("name") != TOOL["name"]:
            return _error(identifier, -32602, "Unknown tool.")
        try:
            result = analyze_path((params.get("arguments") or {}).get("path", ""), allowed_root)
            return {"jsonrpc": "2.0", "id": identifier, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}], "structuredContent": result, "isError": False}}
        except Exception as exc:
            return {"jsonrpc": "2.0", "id": identifier, "result": {"content": [{"type": "text", "text": str(exc)}], "isError": True}}
    if identifier is None:
        return None
    return _error(identifier, -32601, "Method not found.")


def _error(identifier, code, message):
    return {"jsonrpc": "2.0", "id": identifier, "error": {"code": code, "message": message}}


def main():
    default_root = Path(__file__).resolve().parent / "data" / "finance"
    allowed_root = Path(os.environ.get("DAKSH_FINANCE_ROOT", default_root)).expanduser()
    allowed_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    for line in sys.stdin:
        try:
            response = handle(json.loads(line), allowed_root)
        except Exception as exc:
            response = _error(None, -32700, f"Parse error: {exc}")
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
