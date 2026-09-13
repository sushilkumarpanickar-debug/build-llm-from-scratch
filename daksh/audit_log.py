"""Protected, append-only audit records for sensitive DAKSH actions."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Any


class AuditLog:
    """Write event metadata without retaining prompts, responses, or credentials."""

    def __init__(self, data_directory: Path) -> None:
        self.path = data_directory / "audit_events.jsonl"
        self._lock = Lock()

    def record(self, event: str, **metadata: Any) -> None:
        if not event or not event.replace("_", "").isalnum():
            raise ValueError("Audit event must contain only letters, numbers, and underscores.")
        record = {"event": event, "time": time.time(), **metadata}
        encoded = json.dumps(record, separators=(",", ":"), sort_keys=True)
        with self._lock:
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            try:
                previous = self.path.read_text(encoding="utf-8") if self.path.exists() else ""
                with NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=self.path.parent, delete=False
                ) as temporary_file:
                    temporary_file.write(previous)
                    temporary_file.write(f"{encoded}\n")
                    temporary_file.flush()
                    os.fsync(temporary_file.fileno())
                    temporary_path = Path(temporary_file.name)
                os.chmod(temporary_path, 0o600)
                temporary_path.replace(self.path)
            except OSError as error:
                raise RuntimeError("Unable to persist the DAKSH audit log.") from error
