"""Optional communication connectors for DAKSH.

Connectors are disabled until the user supplies local credentials through environment
variables or files under local_workspace/data/connectors. The module stores imported
messages and approval decisions in SQLite, but it never commits secrets or sends data
to paid AI APIs.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

try:
    from .db import SCOPES, utcnow
except ImportError:  # pragma: no cover - direct module execution fallback
    from db import SCOPES, utcnow

ROOT = Path(__file__).resolve().parent
CONNECTOR_DIR = Path(os.environ.get("DAKSH_CONNECTOR_DIR", ROOT / "data" / "connectors"))
GOOGLE_CLIENT_FILE = Path(os.environ.get("DAKSH_GOOGLE_CLIENT_FILE", CONNECTOR_DIR / "google_oauth_client.json"))
GOOGLE_TOKEN_FILE = Path(os.environ.get("DAKSH_GOOGLE_TOKEN_FILE", CONNECTOR_DIR / "google_token.json"))
GOOGLE_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
)
APPROVAL_RE = re.compile(r"^\s*/?(approve|approved|reject|rejected|deny)\s+#?(\d+)\b(?:\s+(.+))?", re.I)
COMMAND_RE = re.compile(r"^\s*/(?:daksh|task|mission)\s+(.+)", re.I | re.S)


class ConnectorUnavailable(RuntimeError):
    """Raised when a connector has not been configured on this Mac."""


def _env_bool(key: str, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(key: str, default: int, minimum: int = 1, maximum: int = 500) -> int:
    try:
        value = int(os.environ.get(key, str(default)))
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def _csv_env(key: str) -> set[str]:
    return {item.strip() for item in os.environ.get(key, "").split(",") if item.strip()}


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))[:50000]


def _connector_state(store, connector: str, key: str, default: str | None = None) -> str | None:
    rows = store.rows(
        "SELECT value FROM connector_state WHERE connector=? AND key=?",
        (connector, key),
    )
    return rows[0]["value"] if rows else default


def _set_connector_state(store, connector: str, key: str, value: Any) -> None:
    store.execute(
        "INSERT INTO connector_state(connector,key,value,updated) VALUES(?,?,?,?) "
        "ON CONFLICT(connector,key) DO UPDATE SET value=excluded.value,updated=excluded.updated",
        (connector, key, str(value), utcnow()),
    )


def _optional_google_available() -> bool:
    try:
        import googleapiclient.discovery  # noqa: F401
        import google.oauth2.credentials  # noqa: F401
        import google.auth.transport.requests  # noqa: F401
        return True
    except Exception:
        return False


def connector_statuses(store=None) -> list[dict[str, Any]]:
    telegram_token = bool(os.environ.get("DAKSH_TELEGRAM_BOT_TOKEN"))
    telegram_allowed = bool(_csv_env("DAKSH_TELEGRAM_ALLOWED_CHATS"))
    google_deps = _optional_google_available()
    google_client = GOOGLE_CLIENT_FILE.is_file()
    google_token = GOOGLE_TOKEN_FILE.is_file()
    whatsapp_verify = bool(os.environ.get("DAKSH_WHATSAPP_VERIFY_TOKEN"))
    whatsapp_secret = bool(os.environ.get("DAKSH_WHATSAPP_APP_SECRET"))
    whatsapp_allowed = bool(_csv_env("DAKSH_WHATSAPP_ALLOWED_NUMBERS"))
    allow_webhooks = _env_bool("DAKSH_ALLOW_EXTERNAL_WEBHOOKS")
    statuses = [
        {
            "id": "telegram",
            "name": "Telegram Bot Instructions",
            "decision": "ready_when_configured",
            "mode": "polling",
            "configured": telegram_token and telegram_allowed,
            "status": "ready" if telegram_token and telegram_allowed else "needs_token_and_allowed_chat",
            "detail": "Receives instructions and approval/rejection commands from allowed Telegram chat IDs.",
            "privacy": "Uses Telegram Bot API; message text leaves Telegram and returns to this Mac.",
            "cost": "free",
        },
        {
            "id": "gmail",
            "name": "Gmail Read-only Inbox",
            "decision": "ready_when_configured",
            "mode": "google_oauth_readonly",
            "configured": google_deps and google_client and google_token,
            "status": "ready" if google_deps and google_client and google_token else "needs_google_oauth_setup",
            "detail": "Imports recent inbox metadata/snippets and treats [DAKSH] or /daksh mail as instructions.",
            "privacy": "Uses Google OAuth read-only scopes; email metadata/snippets are stored locally in SQLite.",
            "cost": "free Google API quota",
        },
        {
            "id": "calendar",
            "name": "Google Calendar Read-only Agenda",
            "decision": "ready_when_configured",
            "mode": "google_oauth_readonly",
            "configured": google_deps and google_client and google_token,
            "status": "ready" if google_deps and google_client and google_token else "needs_google_oauth_setup",
            "detail": "Imports upcoming primary-calendar events for planning and reminders.",
            "privacy": "Uses Google OAuth read-only scopes; event summaries are stored locally in SQLite.",
            "cost": "free Google API quota",
        },
        {
            "id": "whatsapp",
            "name": "WhatsApp Cloud Webhook Intake",
            "decision": "setup_required",
            "mode": "webhook",
            "configured": whatsapp_verify and whatsapp_secret and whatsapp_allowed and allow_webhooks,
            "status": "ready" if whatsapp_verify and whatsapp_secret and whatsapp_allowed and allow_webhooks else "needs_meta_webhook_secret_allowlist_and_explicit_external_webhook",
            "detail": "Can record official WhatsApp Cloud API webhook messages after Meta Business setup and an explicit webhook exposure choice.",
            "privacy": "WhatsApp requires Meta infrastructure and a reachable webhook; disabled by default on the private Mac build.",
            "cost": "Meta WhatsApp pricing may apply outside DAKSH",
        },
    ]
    if store:
        for item in statuses:
            item["last_checked"] = _connector_state(store, item["id"], "last_checked")
    return statuses


def record_external_message(
    store,
    scope: str,
    connector: str,
    external_id: str,
    sender: str = "",
    subject: str = "",
    body: str = "",
    received: str | None = None,
    status: str = "new",
    raw: Any | None = None,
) -> tuple[int, bool]:
    if scope not in SCOPES:
        raise ValueError("Unknown workspace scope")
    with store.connect() as con:
        cur = con.execute(
            "INSERT OR IGNORE INTO external_messages"
            "(scope,connector,external_id,sender,subject,body,received,status,raw_json,created) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                scope,
                connector,
                external_id[:300],
                sender[:500],
                subject[:500],
                body[:20000],
                received or utcnow(),
                status,
                _json(raw or {}),
                utcnow(),
            ),
        )
        if cur.rowcount:
            return int(cur.lastrowid), True
        row = con.execute(
            "SELECT id FROM external_messages WHERE connector=? AND external_id=?",
            (connector, external_id[:300]),
        ).fetchone()
        return int(row["id"]), False


def _create_approval(store, scope: str, connector: str, message_id: int, action: str, detail: str, requested_by: str) -> int:
    rows = store.rows(
        "SELECT id FROM approval_requests WHERE scope=? AND connector=? AND external_message_id=? AND action=? ORDER BY id DESC LIMIT 1",
        (scope, connector, message_id, action),
    )
    if rows:
        return int(rows[0]["id"])
    identifier, _ = store.execute(
        "INSERT INTO approval_requests(scope,connector,external_message_id,action,detail,status,requested_by,created,decided,decision_note) "
        "VALUES(?,?,?,?,?,'pending',?,?,NULL,'')",
        (scope, connector, message_id, action, detail[:8000], requested_by[:500], utcnow()),
    )
    store.execute("UPDATE external_messages SET status='instruction' WHERE id=? AND scope=?", (message_id, scope))
    store.audit(scope, "approval_requested", f"{connector} message {message_id}; approval {identifier}; {action}")
    return int(identifier)


def decide_approval(store, scope: str, approval_id: int, status: str, note: str = "") -> bool:
    normalized = "approved" if status.lower() in {"approve", "approved"} else "rejected"
    _, count = store.execute(
        "UPDATE approval_requests SET status=?,decided=?,decision_note=? WHERE id=? AND scope=? AND status='pending'",
        (normalized, utcnow(), note[:1000], approval_id, scope),
    )
    if count:
        store.audit(scope, f"approval_{normalized}", f"approval {approval_id}; {note[:240]}")
        if normalized == "approved":
            rows = store.rows(
                "SELECT external_message_id FROM approval_requests WHERE id=? AND scope=?",
                (approval_id, scope),
            )
            if rows and rows[0]["external_message_id"]:
                message_id = int(rows[0]["external_message_id"])
                message = store.rows("SELECT status FROM external_messages WHERE id=? AND scope=?", (message_id, scope))
                if message and message[0]["status"] != "staged":
                    stage_message_as_task(store, scope, message_id)
    return bool(count)


def _instruction_from_subject_body(subject: str, body: str, telegram_default: bool = False) -> str:
    content = (body or "").strip()
    subject = (subject or "").strip()
    if telegram_default and content and not content.startswith("/"):
        return content
    command = COMMAND_RE.match(content)
    if command:
        return command.group(1).strip()
    if subject.lower().startswith("[daksh]"):
        return f"{subject}\n\n{content}".strip()
    return ""


def _handle_approval_command(store, scope: str, text: str, connector: str, sender: str) -> tuple[bool, str]:
    match = APPROVAL_RE.match(text or "")
    if not match:
        return False, ""
    decision, approval_id, note = match.groups()
    normalized = "approved" if decision.lower().startswith("approv") else "rejected"
    saved = decide_approval(store, scope, int(approval_id), normalized, f"{connector} approval from {sender}: {note or ''}".strip())
    if saved:
        return True, f"Approval {approval_id} {normalized}."
    return True, f"Approval {approval_id} was not pending in {scope}."


def _telegram_send(token: str, chat_id: str, text: str) -> None:
    if not _env_bool("DAKSH_TELEGRAM_REPLY", True):
        return
    try:
        with httpx.Client(timeout=10) as client:
            client.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": text[:3800]})
    except Exception:
        pass


def poll_telegram(store, scope: str) -> dict[str, Any]:
    token = os.environ.get("DAKSH_TELEGRAM_BOT_TOKEN", "").strip()
    allowed = _csv_env("DAKSH_TELEGRAM_ALLOWED_CHATS")
    if not token or not allowed:
        raise ConnectorUnavailable("Telegram needs DAKSH_TELEGRAM_BOT_TOKEN and DAKSH_TELEGRAM_ALLOWED_CHATS.")
    offset = _connector_state(store, "telegram", "offset", "0") or "0"
    params = {"timeout": 0, "offset": int(offset), "allowed_updates": json.dumps(["message", "edited_message"])}
    imported = 0
    ignored = 0
    approvals = 0
    max_update = int(offset) - 1
    with httpx.Client(timeout=15) as client:
        response = client.get(f"https://api.telegram.org/bot{token}/getUpdates", params=params)
        response.raise_for_status()
        payload = response.json()
    if not payload.get("ok"):
        raise ConnectorUnavailable("Telegram rejected the bot token or polling request.")
    for update in payload.get("result", []):
        update_id = int(update.get("update_id", 0))
        max_update = max(max_update, update_id)
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = str(chat.get("id", ""))
        if chat_id not in allowed:
            ignored += 1
            continue
        sender_info = message.get("from") or chat
        sender = sender_info.get("username") or " ".join(
            str(sender_info.get(part, "")).strip() for part in ("first_name", "last_name") if sender_info.get(part)
        ) or chat_id
        text = (message.get("text") or message.get("caption") or "").strip()
        if not text:
            text = f"[{message.get('content_type') or 'non-text Telegram message'}]"
        received = datetime.fromtimestamp(int(message.get("date") or 0), timezone.utc).isoformat() if message.get("date") else utcnow()
        message_id, inserted = record_external_message(
            store, scope, "telegram", f"{update_id}:{message.get('message_id', '')}", sender, "Telegram instruction", text,
            received, "new", update,
        )
        if inserted:
            imported += 1
        handled, acknowledgement = _handle_approval_command(store, scope, text, "telegram", sender)
        if handled:
            if acknowledgement:
                _telegram_send(token, chat_id, acknowledgement)
            approvals += 1
            continue
        instruction = _instruction_from_subject_body("Telegram instruction", text, telegram_default=True)
        if instruction and inserted:
            approval_id = _create_approval(store, scope, "telegram", message_id, "telegram_instruction", instruction, sender)
            _telegram_send(
                token,
                chat_id,
                f"DAKSH received the instruction and staged approval #{approval_id}. Reply `approve {approval_id}` or `reject {approval_id}` when ready.",
            )
    if max_update >= int(offset):
        _set_connector_state(store, "telegram", "offset", max_update + 1)
    _set_connector_state(store, "telegram", "last_checked", utcnow())
    return {"connector": "telegram", "imported": imported, "ignored": ignored, "approval_commands": approvals}


def _google_service(api: str, version: str):
    if not _optional_google_available():
        raise ConnectorUnavailable("Install Google connector packages with setup_mac.sh first.")
    if not GOOGLE_CLIENT_FILE.is_file() or not GOOGLE_TOKEN_FILE.is_file():
        raise ConnectorUnavailable("Run scripts/setup_google_connectors.py after placing google_oauth_client.json in the connector folder.")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    credentials = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), GOOGLE_SCOPES)
    if not credentials.valid:
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            CONNECTOR_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
            GOOGLE_TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
            os.chmod(GOOGLE_TOKEN_FILE, 0o600)
        else:
            raise ConnectorUnavailable("Google token is missing required scopes; rerun scripts/setup_google_connectors.py.")
    return build(api, version, credentials=credentials, cache_discovery=False)


def poll_gmail(store, scope: str) -> dict[str, Any]:
    service = _google_service("gmail", "v1")
    query = os.environ.get("DAKSH_GMAIL_QUERY", "newer_than:7d")
    limit = _env_int("DAKSH_GMAIL_MAX_RESULTS", 10, 1, 50)
    response = service.users().messages().list(userId="me", labelIds=["INBOX"], q=query, maxResults=limit).execute()
    imported = 0
    instructions = 0
    for item in reversed(response.get("messages", [])):
        message = service.users().messages().get(
            userId="me", id=item["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h.get("name", "").lower(): h.get("value", "") for h in message.get("payload", {}).get("headers", [])}
        received = utcnow()
        if message.get("internalDate"):
            received = datetime.fromtimestamp(int(message["internalDate"]) / 1000, timezone.utc).isoformat()
        subject = headers.get("subject", "")
        sender = headers.get("from", "")
        body = message.get("snippet", "")
        message_id, inserted = record_external_message(store, scope, "gmail", message["id"], sender, subject, body, received, "new", message)
        if inserted:
            imported += 1
            instruction = _instruction_from_subject_body(subject, body)
            if instruction:
                _create_approval(store, scope, "gmail", message_id, "email_instruction", instruction, sender)
                instructions += 1
    _set_connector_state(store, "gmail", "last_checked", utcnow())
    return {"connector": "gmail", "imported": imported, "instructions": instructions, "query": query}


def _event_time(value: dict[str, Any]) -> str:
    return value.get("dateTime") or (value.get("date") + "T00:00:00+00:00" if value.get("date") else "")


def _record_calendar_event(store, scope: str, event: dict[str, Any]) -> bool:
    external_id = str(event.get("id", ""))[:300]
    if not external_id:
        return False
    start = _event_time(event.get("start", {}))
    end = _event_time(event.get("end", {}))
    now = utcnow()
    with store.connect() as con:
        cur = con.execute(
            "INSERT INTO calendar_events(scope,connector,external_id,title,starts_at,ends_at,location,link,status,raw_json,created,updated) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(connector,external_id) DO UPDATE SET title=excluded.title,starts_at=excluded.starts_at,"
            "ends_at=excluded.ends_at,location=excluded.location,link=excluded.link,status=excluded.status,raw_json=excluded.raw_json,updated=excluded.updated",
            (
                scope,
                "google_calendar",
                external_id,
                str(event.get("summary") or "Untitled event")[:500],
                start,
                end,
                str(event.get("location") or "")[:500],
                str(event.get("htmlLink") or "")[:1000],
                str(event.get("status") or "confirmed")[:100],
                _json(event),
                now,
                now,
            ),
        )
        return bool(cur.rowcount)


def poll_calendar(store, scope: str) -> dict[str, Any]:
    service = _google_service("calendar", "v3")
    days = _env_int("DAKSH_CALENDAR_LOOKAHEAD_DAYS", 14, 1, 90)
    limit = _env_int("DAKSH_CALENDAR_MAX_RESULTS", 20, 1, 100)
    time_min = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    time_max = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")
    response = service.events().list(
        calendarId="primary", timeMin=time_min, timeMax=time_max, maxResults=limit,
        singleEvents=True, orderBy="startTime",
    ).execute()
    imported = sum(1 for event in response.get("items", []) if _record_calendar_event(store, scope, event))
    _set_connector_state(store, "calendar", "last_checked", utcnow())
    return {"connector": "calendar", "imported_or_updated": imported, "lookahead_days": days}


def process_whatsapp_webhook(store, scope: str, payload: dict[str, Any]) -> dict[str, Any]:
    allowed = _csv_env("DAKSH_WHATSAPP_ALLOWED_NUMBERS")
    imported = 0
    ignored = 0
    instructions = 0
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            contact_names = {
                str(contact.get("wa_id")): contact.get("profile", {}).get("name", "")
                for contact in value.get("contacts", [])
            }
            for message in value.get("messages", []):
                sender_number = str(message.get("from", ""))
                if allowed and sender_number not in allowed:
                    ignored += 1
                    continue
                text = message.get("text", {}).get("body") or message.get("button", {}).get("text") or f"[{message.get('type', 'message')}]"
                received = utcnow()
                if message.get("timestamp"):
                    received = datetime.fromtimestamp(int(message["timestamp"]), timezone.utc).isoformat()
                message_id, inserted = record_external_message(
                    store, scope, "whatsapp", str(message.get("id", "")), contact_names.get(sender_number, sender_number),
                    "WhatsApp message", text, received, "new", message,
                )
                if inserted:
                    imported += 1
                    instruction = _instruction_from_subject_body("WhatsApp message", text, telegram_default=True)
                    if instruction:
                        _create_approval(store, scope, "whatsapp", message_id, "whatsapp_instruction", instruction, sender_number)
                        instructions += 1
    return {"connector": "whatsapp", "imported": imported, "ignored": ignored, "instructions": instructions}


def poll_all(store, scope: str, connector: str | None = None) -> dict[str, Any]:
    selected = [connector] if connector else ["telegram", "gmail", "calendar"]
    results = []
    for name in selected:
        try:
            if name == "telegram":
                results.append(poll_telegram(store, scope))
            elif name == "gmail":
                results.append(poll_gmail(store, scope))
            elif name == "calendar":
                results.append(poll_calendar(store, scope))
            elif name == "whatsapp":
                raise ConnectorUnavailable("WhatsApp uses webhook intake; configure Meta and POST webhook events instead of polling.")
            else:
                raise ConnectorUnavailable(f"Unknown connector {name}.")
        except ConnectorUnavailable as exc:
            results.append({"connector": name, "skipped": True, "reason": str(exc)})
        except Exception as exc:
            results.append({"connector": name, "error": str(exc)[:500]})
        finally:
            if name in {"telegram", "gmail", "calendar"}:
                _set_connector_state(store, name, "last_attempt", utcnow())
    return {"status": "checked", "results": results, "communications": snapshot(store, scope)}


def snapshot(store, scope: str) -> dict[str, Any]:
    inbox = store.rows(
        "SELECT id,scope,connector,external_id,sender,subject,body,received,status,created "
        "FROM external_messages WHERE scope=? ORDER BY received DESC,id DESC LIMIT 75",
        (scope,),
    )
    approvals = store.rows(
        "SELECT id,scope,connector,external_message_id,action,detail,status,requested_by,created,decided,decision_note "
        "FROM approval_requests WHERE scope=? ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END,id DESC LIMIT 75",
        (scope,),
    )
    calendar = store.rows(
        "SELECT id,scope,connector,external_id,title,starts_at,ends_at,location,link,status,updated "
        "FROM calendar_events WHERE scope=? AND starts_at>=? ORDER BY starts_at LIMIT 40",
        (scope, datetime.now(timezone.utc).date().isoformat()),
    )
    return {
        "connectors": connector_statuses(store),
        "inbox": inbox,
        "approvals": approvals,
        "calendar": calendar,
        "pending_approvals": sum(1 for item in approvals if item["status"] == "pending"),
        "unread_messages": sum(1 for item in inbox if item["status"] in {"new", "instruction"}),
    }


def update_message_status(store, scope: str, message_id: int, status: str) -> bool:
    if status not in {"new", "instruction", "reviewed", "archived", "staged"}:
        raise ValueError("Unknown message status")
    _, count = store.execute("UPDATE external_messages SET status=? WHERE id=? AND scope=?", (status, message_id, scope))
    return bool(count)


def stage_message_as_task(store, scope: str, message_id: int) -> int:
    rows = store.rows(
        "SELECT * FROM external_messages WHERE id=? AND scope=?",
        (message_id, scope),
    )
    if not rows:
        raise ValueError("Message not found in this workspace")
    message = rows[0]
    if message["status"] == "staged":
        raise ValueError("This message is already staged as a mission")
    title = f"{message['connector']}: {message['subject'] or message['body'][:80]}"[:180]
    plan = (
        f"External instruction captured from {message['connector']} by {message['sender']}.\n\n"
        "Review the instruction, confirm any external action, and then execute through DAKSH only after the required approval is recorded.\n\n"
        f"Instruction:\n{message['body']}"
    )
    identifier, _ = store.execute(
        "INSERT INTO tasks(scope,title,status,plan,created) VALUES(?,?,?,?,?)",
        (scope, title, "planned", plan[:20000], utcnow()),
    )
    update_message_status(store, scope, message_id, "staged")
    store.audit(scope, "external_message_staged", f"message {message_id}; task {identifier}")
    return int(identifier)
