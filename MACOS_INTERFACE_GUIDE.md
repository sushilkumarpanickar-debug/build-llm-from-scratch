# DAKSH macOS Interface Guide

## Open the real app in Xcode

Open `macos/DAKSH/DAKSH.xcodeproj`, select the `DAKSH` scheme, and press **Run**.

If Xcode shows `.cbmignore`, `.gitignore`, or plain source files, it means Xcode opened the repository folder. Use **File > Open...** and choose `macos/DAKSH/DAKSH.xcodeproj`.

## What the app does

The DAKSH Mac app is a native SwiftUI/WebKit shell for the private local second-brain service. On launch it:

- opens the `codex/daksh-local-workspace` branch;
- fetches and fast-forwards from GitHub;
- starts the local FastAPI server on `127.0.0.1:9001`;
- loads the DAKSH JARVIS-style UI in a Mac window;
- grants microphone access only to local `127.0.0.1`/`localhost` origins;
- checks GitHub every ten minutes while open.

Local edits are not overwritten. If Git cannot fast-forward, the app shows the Git message in the title area so you can review the checkout in Xcode or Terminal.

## Build a packaged app

From the repository root:

```sh
zsh scripts/build_macos_app.sh
```

The command generates the app icon from `local_workspace/static/snns_emblem.png`, builds the Xcode target, signs the copied app for local running, and writes:

- `dist/DAKSH.app`
- `dist/DAKSH-macOS-app.zip`

## Setup requirements

Run this once from the repository root if the app reports that `.venv/bin/python` is missing:

```sh
./setup_mac.sh
ollama pull nomic-embed-text
```

Ollama should be running locally. DAKSH will use an installed free local chat model and `nomic-embed-text` for embeddings.
