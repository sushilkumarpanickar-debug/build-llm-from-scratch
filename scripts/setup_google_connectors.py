#!/usr/bin/env python3
"""Authorize DAKSH's read-only Gmail and Google Calendar connection."""
from __future__ import annotations

import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow


ROOT = Path(__file__).resolve().parents[1]
CONNECTOR_DIR = Path(os.environ.get("DAKSH_CONNECTOR_DIR", ROOT / "local_workspace" / "data" / "connectors"))
CLIENT_FILE = Path(os.environ.get("DAKSH_GOOGLE_CLIENT_FILE", CONNECTOR_DIR / "google_oauth_client.json"))
TOKEN_FILE = Path(os.environ.get("DAKSH_GOOGLE_TOKEN_FILE", CONNECTOR_DIR / "google_token.json"))
SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
)


def main() -> None:
    if not CLIENT_FILE.is_file():
        raise SystemExit(
            f"Google OAuth client file not found: {CLIENT_FILE}\n"
            "Download a Desktop app OAuth client JSON from Google Cloud and save it at that location."
        )
    CONNECTOR_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
    credentials = flow.run_local_server(host="127.0.0.1", port=0, open_browser=True)
    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    os.chmod(TOKEN_FILE, 0o600)
    print(f"DAKSH Gmail and Calendar read-only access is ready: {TOKEN_FILE}")


if __name__ == "__main__":
    main()
