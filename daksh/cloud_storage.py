"""Persistent storage for DAKSH data synchronized through iCloud Drive."""

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Any, Dict, List

from loguru import logger


class InteractionHistoryStore:
    """Store interaction history in a file that iCloud Drive can synchronize."""

    def __init__(self, data_directory: Path):
        self.path = data_directory / "interaction_history.json"
        self._lock = Lock()

    def load(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []

        try:
            with self.path.open(encoding="utf-8") as history_file:
                history = json.load(history_file)
        except (OSError, json.JSONDecodeError) as error:
            logger.error(f"Unable to load DAKSH interaction history: {error}")
            return []

        if not isinstance(history, list):
            logger.error("DAKSH interaction history must contain a JSON list")
            return []

        return history

    def save(self, history: List[Dict[str, Any]]) -> None:
        with self._lock:
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            try:
                with NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=self.path.parent,
                    delete=False,
                ) as temporary_file:
                    json.dump(history, temporary_file, ensure_ascii=False, indent=2)
                    temporary_path = Path(temporary_file.name)

                os.chmod(temporary_path, 0o600)
                temporary_path.replace(self.path)
            except OSError as error:
                logger.error(f"Unable to save DAKSH interaction history: {error}")
                raise
