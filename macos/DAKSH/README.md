# DAKSH Mac App

Open `DAKSH.xcodeproj` in Xcode and run the `DAKSH` target. The app launches a native macOS window, syncs `origin/codex/daksh-local-workspace`, restarts the local Python server, and loads `http://127.0.0.1:9001` inside WebKit.

The app expects this repository at `/Users/mayanagari/Documents/Codex/2026-09-13/mak/work/build-llm-from-scratch` by default. Use the folder button in the title bar if the checkout moves.

The launcher checks GitHub when it starts and every ten minutes while open. It only fast-forwards; local edits are not overwritten. If `.venv/bin/python` is missing, use **Run Local Setup** in the app or run `./setup_mac.sh` from the repository root.
