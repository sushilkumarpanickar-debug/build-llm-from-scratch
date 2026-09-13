#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DEFAULT_BINARY="/Users/mayanagari/Documents/Codex/2026-09-07/we-x20/work/pilot/runtime/cbm/codebase-memory-mcp"
CBM_BINARY=${DAKSH_CBM_BINARY:-$DEFAULT_BINARY}
CBM_CACHE_DIR=${DAKSH_CBM_CACHE_DIR:-$PROJECT_ROOT/local_workspace/data/codebase-memory}

if [ ! -x "$CBM_BINARY" ]; then
  echo "DAKSH Codebase Memory binary is unavailable: $CBM_BINARY" >&2
  echo "Set DAKSH_CBM_BINARY to the reviewed codebase-memory-mcp 0.10.8 binary." >&2
  exit 1
fi

mkdir -p "$CBM_CACHE_DIR"
cd "$PROJECT_ROOT"
export CBM_CACHE_DIR
exec "$CBM_BINARY" --tool-profile=analysis
