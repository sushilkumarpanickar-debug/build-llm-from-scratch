import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from daksh.opencode_agent import OpenCodeAgent, OpenCodeError
from daksh.web_dashboard import create_daksh_dashboard


ROOT = Path(__file__).resolve().parent.parent


class OpenCodeAgentTests(unittest.TestCase):
    def setUp(self):
        self.agent = OpenCodeAgent(ROOT, timeout_seconds=5, max_output_bytes=1024)

    def test_rejects_a_workspace_other_than_repository_root(self):
        with self.assertRaises(OpenCodeError):
            OpenCodeAgent(ROOT / "daksh")

    def test_rejects_non_string_and_oversized_prompts(self):
        with self.assertRaisesRegex(ValueError, "must be a string"):
            self.agent.submit(None)
        with self.assertRaisesRegex(ValueError, "character limit"):
            self.agent.submit("x" * 12_001)

    @patch("daksh.opencode_agent.shutil.which", return_value="/usr/local/bin/tool")
    @patch("daksh.opencode_agent.subprocess.run")
    def test_submits_local_only_command(self, run, _which):
        run.side_effect = [
            subprocess.CompletedProcess(["ollama"], 0, "", ""),
            subprocess.CompletedProcess(["opencode"], 0, '{"type":"text"}', ""),
        ]

        job = self.agent.submit("Fix the focused test")
        self.agent._executor.shutdown(wait=True)

        command_call = run.call_args_list[1]
        self.assertEqual(
            command_call.args[0],
            ["opencode", "run", "--model", "ollama/qwen2.5:3b", "--format", "json", "--", "Fix the focused test"],
        )
        self.assertEqual(command_call.kwargs["cwd"], ROOT)
        config = command_call.kwargs["env"]["OPENCODE_CONFIG_CONTENT"]
        self.assertIn('"enabled_providers":["ollama"]', config)
        self.assertIn('"external_directory":"deny"', config)
        self.assertEqual(command_call.kwargs["env"]["OPENCODE_DISABLE_PROJECT_CONFIG"], "true")
        self.assertEqual(job.state, "completed")

    @patch("daksh.opencode_agent.shutil.which", return_value=None)
    def test_explains_missing_opencode_cli(self, _which):
        with self.assertRaisesRegex(OpenCodeError, "OpenCode CLI is unavailable"):
            self.agent.submit("Make a change")

    @patch("daksh.opencode_agent.shutil.which", return_value="/usr/local/bin/tool")
    @patch("daksh.opencode_agent.subprocess.run")
    def test_marks_job_as_timed_out(self, run, _which):
        run.side_effect = [
            subprocess.CompletedProcess(["ollama"], 0, "", ""),
            subprocess.TimeoutExpired(["opencode"], 5, output="partial output"),
        ]

        job = self.agent.submit("Take too long")
        self.agent._executor.shutdown(wait=True)

        self.assertEqual(job.state, "timed_out")
        self.assertIn("runtime limit", job.error)
        self.assertEqual(job.output, "partial output")

    def test_truncates_exposed_output(self):
        self.assertIn("output truncated", self.agent._truncate("x" * 2_000))


class OpenCodeDashboardTests(unittest.TestCase):
    def setUp(self):
        self.app = create_daksh_dashboard()
        self.client = self.app.test_client()

    def test_rejects_invalid_job_submission(self):
        response = self.client.post("/api/opencode/jobs", json={"prompt": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("must not be empty", response.get_json()["error"])

    def test_rejects_invalid_job_identifier(self):
        response = self.client.get("/api/opencode/jobs/not-an-id")
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)


if __name__ == "__main__":
    unittest.main()
