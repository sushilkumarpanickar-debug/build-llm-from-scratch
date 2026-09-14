# DAKSH Mac App

Open `macos/DAKSH/DAKSH.xcodeproj` in Xcode, select the `DAKSH` scheme, and press **Run**. If Xcode shows only files such as `.cbmignore`, you opened the repository folder instead of the app project.

The app is a native macOS shell for the local DAKSH second-brain service. It opens a real Mac window, starts the private FastAPI service on `127.0.0.1:9001`, and renders the JARVIS-style DAKSH UI through WebKit.

On launch, the app opens the `codex/daksh-local-workspace` branch, fetches GitHub, fast-forwards the checkout, restarts the local server, and loads the UI. It checks GitHub again every ten minutes while the app is open. Local uncommitted edits are not overwritten; if a fast-forward is blocked, the title bar shows the Git message so you can review it in Xcode or Terminal.

The default repository path is `/Users/mayanagari/Documents/Codex/2026-09-13/mak/work/build-llm-from-scratch`. Use the folder button in the DAKSH title bar if the checkout moves.

If `.venv/bin/python` is missing, use **Run Local Setup** inside the app or run this from the repository root:

```sh
./setup_mac.sh
```

To build and package the app from Terminal:

```sh
zsh scripts/build_macos_app.sh
```

That command produces `dist/DAKSH.app` and `dist/DAKSH-macOS-app.zip`.
