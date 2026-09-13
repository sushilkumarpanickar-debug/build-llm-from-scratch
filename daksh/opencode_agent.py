"""Restricted, local-only OpenCode jobs for the DAKSH dashboard."""

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


class OpenCodeError(RuntimeError):
    """Raised when an OpenCode job cannot be safely started."""


JobState = Literal["pending_approval", "queued", "running", "completed", "failed", "timed_out", "denied"]
MAX_PROMPT_LENGTH = 12_000


@dataclass
class OpenCodeJob:
    """A bounded record of a non-interactive coding-agent invocation."""

    id: str
    prompt: str
    state: JobState = "queued"
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    returncode: int | None = None
    output: str = ""
    error: str | None = None
    approval_id: str | None = None

    def public(self) -> dict[str, object]:
        return {
            "id": self.id,
            "state": self.state,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "returncode": self.returncode,
            "output": self.output,
            "error": self.error,
            "approval_id": self.approval_id,
        }


class OpenCodeAgent:
    """Runs one local Ollama-backed OpenCode job at a time in this repository."""

    def __init__(
        self,
        workspace: Path,
        *,
        command: str = "opencode",
        model: str = "qwen2.5:3b",
        timeout_seconds: int = 300,
        max_output_bytes: int = 64 * 1024,
    ) -> None:
        expected_workspace = Path(__file__).resolve().parent.parent
        self.workspace = workspace.expanduser().resolve()
        if self.workspace != expected_workspace:
            raise OpenCodeError("OpenCode workspace must be exactly the DAKSH repository root.")
        if timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")
        if max_output_bytes < 1024:
            raise ValueError("max_output_bytes must be at least 1024")
        self.command = command
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes
        self._jobs: dict[str, OpenCodeJob] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="daksh-opencode")

    def submit(self, prompt: str) -> OpenCodeJob:
        """Queue a prompt immediately for backward-compatible direct callers."""
        job = self.create_pending(prompt)
        self.approve(job.id)
        return job

    def create_pending(self, prompt: str) -> OpenCodeJob:
        """Create an approval-gated job without starting an OpenCode process."""
        if not isinstance(prompt, str):
            raise ValueError("Prompt must be a string.")
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Prompt must not be empty.")
        if len(prompt) > MAX_PROMPT_LENGTH:
            raise ValueError(f"Prompt exceeds the {MAX_PROMPT_LENGTH:,} character limit.")
        self._verify_dependencies()
        job = OpenCodeJob(id=uuid.uuid4().hex, prompt=prompt, state="pending_approval")
        with self._lock:
            self._jobs[job.id] = job
        return job

    def approve(self, job_id: str) -> bool:
        """Start a job exactly once after its approval service accepts it."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.state != "pending_approval":
                return False
            job.state = "queued"
        self._executor.submit(self._run, job)
        return True

    def get(self, job_id: str) -> OpenCodeJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _verify_dependencies(self) -> None:
        if shutil.which(self.command) is None:
            raise OpenCodeError(
                "OpenCode CLI is unavailable. Install it with `brew install anomalyco/tap/opencode`."
            )
        if shutil.which("ollama") is None:
            raise OpenCodeError("Ollama CLI is unavailable. Install Ollama, start it, then run `ollama pull qwen2.5:3b`.")
        try:
            probe = subprocess.run(
                ["ollama", "show", self.model],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
        except subprocess.TimeoutExpired as error:
            raise OpenCodeError("Ollama did not respond within 15 seconds.") from error
        if probe.returncode != 0:
            raise OpenCodeError(f"Ollama model `{self.model}` is unavailable. Run `ollama pull {self.model}`.")

    def _environment(self) -> dict[str, str]:
        config = {
            "$schema": "https://opencode.ai/config.json",
            "enabled_providers": ["ollama"],
            "model": f"ollama/{self.model}",
            "share": "disabled",
            "permission": {
                "read": "allow",
                "edit": "allow",
                "bash": "allow",
                "external_directory": "deny",
                "webfetch": "deny",
                "websearch": "deny",
            },
            "provider": {
                "ollama": {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": "Ollama (local)",
                    "options": {"baseURL": "http://localhost:11434/v1"},
                    "models": {self.model: {"name": self.model}},
                }
            },
            "tool_output": {"max_lines": 500, "max_bytes": self.max_output_bytes},
        }
        env = {key: value for key, value in os.environ.items() if key in {"PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE"}}
        env.update(
            {
                "OPENCODE_CONFIG_CONTENT": json.dumps(config, separators=(",", ":")),
                "OPENCODE_DISABLE_PROJECT_CONFIG": "true",
                "OPENCODE_DISABLE_AUTOUPDATE": "true",
            }
        )
        return env

    def _run(self, job: OpenCodeJob) -> None:
        job.state = "running"
        job.started_at = time.time()
        command = [self.command, "run", "--model", f"ollama/{self.model}", "--format", "json", "--", job.prompt]
        try:
            completed = subprocess.run(
                command,
                cwd=self.workspace,
                env=self._environment(),
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            output = (error.stdout or "") + (error.stderr or "")
            job.output = self._truncate(output)
            job.error = f"OpenCode exceeded the {self.timeout_seconds}-second runtime limit."
            job.state = "timed_out"
        else:
            job.returncode = completed.returncode
            job.output = self._truncate((completed.stdout or "") + (completed.stderr or ""))
            if completed.returncode == 0:
                job.state = "completed"
            else:
                job.state = "failed"
                job.error = f"OpenCode exited with status {completed.returncode}."
        finally:
            job.completed_at = time.time()

    def _truncate(self, output: str | bytes) -> str:
        """Bound the output retained in memory and exposed by the API."""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        encoded = output.encode("utf-8")
        if len(encoded) <= self.max_output_bytes:
            return output
        clipped = encoded[: self.max_output_bytes].decode("utf-8", errors="ignore")
        return f"{clipped}\n[DAKSH: output truncated at {self.max_output_bytes} bytes]"
