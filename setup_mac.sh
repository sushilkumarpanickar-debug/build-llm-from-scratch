#!/bin/zsh
set -eu

REPO_DIR="${0:A:h}"
cd "$REPO_DIR"

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(sys.version_info < (3,11))'; then
  PYTHON_BIN="$(command -v python3)"
else
  CODEX_PYTHON="${HOME}/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
  if [[ -x "$CODEX_PYTHON" ]]; then
    PYTHON_BIN="$CODEX_PYTHON"
  fi
fi

if [[ -z "$PYTHON_BIN" ]]; then
  print "Python 3.11 or newer is required. Install it from python.org or with Homebrew."
  command -v brew >/dev/null 2>&1 || print "Homebrew is not currently installed."
  exit 1
fi

if ! command -v ollama >/dev/null 2>&1; then
  print "Ollama is required. Install the macOS app from https://ollama.com/download"
  exit 1
fi

"$PYTHON_BIN" -m venv --system-site-packages .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements-local.txt
mkdir -p local_workspace/data/documents local_workspace/data/finance
chmod 700 local_workspace/data local_workspace/data/documents local_workspace/data/finance

print ""
print "Local environment is ready."
print "Install the free models if they are missing:"
print "  ollama pull qwen3:8b"
print "  ollama pull nomic-embed-text"
print ""
print "Start DAKSH:"
print "  .venv/bin/python -m local_workspace.server"
print "Then open http://127.0.0.1:9001"
