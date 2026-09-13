"""Telegram-backed approval gates for sensitive local DAKSH actions."""

from __future__ import annotations

import json
import os
import re
import hashlib
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from daksh.audit_log import AuditLog

class TelegramApprovalError(RuntimeError):
    """Raised when the Telegram approval gate cannot safely operate."""


@dataclass(frozen=True)
class Approval:
    """A pending or resolved approval request."""

    id: str
    job_id: str
    status: str
    created_at: float
    expires_at: float
    prompt_digest: str


class TelegramApprovalService:
    """Persist approvals and accept exact commands from one Telegram chat."""

    _COMMAND = re.compile(r"^(APPROVE|DENY) ([0-9a-f]{32})$")

    def __init__(
        self,
        *,
        bot_token: str | None,
        allowed_chat_id: str | None,
        data_directory: Path,
        on_approved: Callable[[str], None],
        on_denied: Callable[[str], None] | None = None,
        audit_log: AuditLog | None = None,
        expires_seconds: int = 900,
        request_timeout_seconds: float = 10,
    ) -> None:
        self.bot_token = bot_token.strip() if isinstance(bot_token, str) else ""
        self.allowed_chat_id = allowed_chat_id.strip() if isinstance(allowed_chat_id, str) else ""
        self.path = data_directory / "telegram_approvals.json"
        self.on_approved = on_approved
        self.on_denied = on_denied
        self.audit_log = audit_log
        self.expires_seconds = expires_seconds
        self.request_timeout_seconds = request_timeout_seconds
        self._lock = threading.RLock()
        self._polling_thread: threading.Thread | None = None
        self._stop_polling = threading.Event()

    def configuration_error(self) -> str | None:
        if not self.bot_token:
            return "Telegram approval is not configured: set TELEGRAM_BOT_TOKEN."
        if not self.allowed_chat_id:
            return "Telegram approval is not configured: set TELEGRAM_ALLOWED_CHAT_ID."
        if self.expires_seconds < 1:
            return "Telegram approval expiry must be positive."
        if not 0 < self.request_timeout_seconds <= 60:
            return "Telegram approval HTTP timeout must be between 0 and 60 seconds."
        return None

    def request_approval(self, job_id: str, prompt: str) -> Approval:
        """Persist and send an approval request to the sole authorized chat."""
        self._require_configuration()
        now = time.time()
        approval = Approval(
            id=uuid.uuid4().hex,
            job_id=job_id,
            status="pending",
            created_at=now,
            expires_at=now + self.expires_seconds,
            prompt_digest=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        )
        with self._lock:
            state = self._load()
            self._expire(state, now)
            state["approvals"][approval.id] = {
                "job_id": job_id,
                "status": approval.status,
                "created_at": approval.created_at,
                "expires_at": approval.expires_at,
                "prompt_digest": approval.prompt_digest,
            }
            self._save(state)
        if self.audit_log:
            self.audit_log.record(
                "approval_requested",
                approval_id=approval.id,
                job_id=job_id,
                prompt_digest=approval.prompt_digest,
            )
        excerpt = prompt.replace("\n", " ").strip()[:500]
        message = (
            f"DAKSH OpenCode approval required\n"
            f"Request: {approval.id}\n"
            f"Prompt: {excerpt}\n\n"
            f"Reply exactly: APPROVE {approval.id}\n"
            f"or: DENY {approval.id}"
        )
        self._telegram_request("sendMessage", {"chat_id": self.allowed_chat_id, "text": message})
        return approval

    def poll_once(self) -> int:
        """Fetch updates and resolve valid commands from the authorized chat."""
        self._require_configuration()
        with self._lock:
            state = self._load()
            self._expire(state, time.time())
            offset = state["telegram_offset"]
        response = self._telegram_request("getUpdates", {"offset": offset, "timeout": 0})
        updates = response.get("result")
        if not isinstance(updates, list):
            raise TelegramApprovalError("Telegram returned an invalid updates response.")

        approved_jobs: list[str] = []
        denied_jobs: list[str] = []
        with self._lock:
            state = self._load()
            self._expire(state, time.time())
            for update in updates:
                if not isinstance(update, dict) or not isinstance(update.get("update_id"), int):
                    continue
                state["telegram_offset"] = max(state["telegram_offset"], update["update_id"] + 1)
                message = update.get("message")
                if not isinstance(message, dict):
                    continue
                chat = message.get("chat")
                text = message.get("text")
                if not isinstance(chat, dict) or str(chat.get("id")) != self.allowed_chat_id:
                    continue
                if not isinstance(text, str):
                    continue
                matched = self._COMMAND.fullmatch(text)
                if not matched:
                    continue
                action, approval_id = matched.groups()
                record = state["approvals"].get(approval_id)
                if not isinstance(record, dict) or record.get("status") != "pending":
                    continue
                if record.get("expires_at", 0) <= time.time():
                    record["status"] = "expired"
                    continue
                record["status"] = "approved" if action == "APPROVE" else "denied"
                if self.audit_log:
                    self.audit_log.record(
                        "approval_resolved",
                        approval_id=approval_id,
                        job_id=record.get("job_id"),
                        outcome=record["status"],
                        prompt_digest=record.get("prompt_digest"),
                    )
                if action == "APPROVE" and isinstance(record.get("job_id"), str):
                    approved_jobs.append(record["job_id"])
                if action == "DENY" and isinstance(record.get("job_id"), str):
                    denied_jobs.append(record["job_id"])
            self._save(state)
        for job_id in approved_jobs:
            self.on_approved(job_id)
        if self.on_denied:
            for job_id in denied_jobs:
                self.on_denied(job_id)
        return len(approved_jobs)

    def start_polling(self, interval_seconds: float = 2) -> None:
        """Start bounded, daemonized polling when Telegram is configured."""
        if self.configuration_error() is not None:
            return
        if interval_seconds <= 0:
            raise ValueError("Polling interval must be positive.")
        with self._lock:
            if self._polling_thread and self._polling_thread.is_alive():
                return
            self._stop_polling.clear()
            self._polling_thread = threading.Thread(
                target=self._poll_loop, args=(interval_seconds,), daemon=True, name="daksh-telegram-approvals"
            )
            self._polling_thread.start()

    def _poll_loop(self, interval_seconds: float) -> None:
        while not self._stop_polling.is_set():
            try:
                self.poll_once()
            except TelegramApprovalError:
                pass
            self._stop_polling.wait(interval_seconds)

    def _require_configuration(self) -> None:
        error = self.configuration_error()
        if error:
            raise TelegramApprovalError(error)

    def _telegram_request(self, method: str, payload: dict[str, object]) -> dict[str, object]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"https://api.telegram.org/bot{self.bot_token}/{method}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.request_timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError, ValueError) as error:
            raise TelegramApprovalError("Telegram request failed; check bot configuration and connectivity.") from error
        if not isinstance(data, dict) or data.get("ok") is not True:
            raise TelegramApprovalError("Telegram rejected the request; check bot configuration and connectivity.")
        return data

    def _load(self) -> dict[str, object]:
        if not self.path.exists():
            return {"telegram_offset": 0, "approvals": {}}
        try:
            with self.path.open(encoding="utf-8") as state_file:
                state = json.load(state_file)
        except (OSError, json.JSONDecodeError) as error:
            raise TelegramApprovalError("Unable to read persisted Telegram approvals.") from error
        if not isinstance(state, dict) or not isinstance(state.get("approvals"), dict):
            raise TelegramApprovalError("Persisted Telegram approvals are invalid.")
        if not isinstance(state.get("telegram_offset"), int):
            state["telegram_offset"] = 0
        return state

    def _save(self, state: dict[str, object]) -> None:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as temporary_file:
                json.dump(state, temporary_file, separators=(",", ":"))
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
                temporary_path = Path(temporary_file.name)
            os.chmod(temporary_path, 0o600)
            temporary_path.replace(self.path)
        except OSError as error:
            raise TelegramApprovalError("Unable to persist Telegram approvals.") from error

    @staticmethod
    def _expire(state: dict[str, object], now: float) -> None:
        approvals = state["approvals"]
        assert isinstance(approvals, dict)
        for record in approvals.values():
            if isinstance(record, dict) and record.get("status") == "pending" and record.get("expires_at", 0) <= now:
                record["status"] = "expired"
