import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from daksh.opencode_agent import OpenCodeAgent
from daksh.telegram_approval import TelegramApprovalError, TelegramApprovalService


ROOT = Path(__file__).resolve().parent.parent
TEST_DATA = ROOT / "tests" / ".telegram-approval-test-data"


def telegram_response(payload):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    return response


class TelegramApprovalServiceTests(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TEST_DATA, ignore_errors=True)
        self.approved_jobs = []
        self.service = TelegramApprovalService(
            bot_token="test-token",
            allowed_chat_id="12345",
            data_directory=TEST_DATA,
            on_approved=self.approved_jobs.append,
            expires_seconds=60,
            request_timeout_seconds=3,
        )

    def tearDown(self):
        shutil.rmtree(TEST_DATA, ignore_errors=True)

    @patch("daksh.telegram_approval.urlopen")
    def test_sends_only_to_configured_chat_and_approves_exact_command(self, urlopen_mock):
        urlopen_mock.side_effect = [
            telegram_response({"ok": True, "result": {"message_id": 1}}),
            telegram_response({"ok": True, "result": []}),
        ]
        approval = self.service.request_approval("job-1", "Fix a focused test")

        sent_payload = json.loads(urlopen_mock.call_args_list[0].args[0].data.decode("utf-8"))
        self.assertEqual(sent_payload["chat_id"], "12345")
        self.assertIn(f"APPROVE {approval.id}", sent_payload["text"])
        self.assertEqual(urlopen_mock.call_args_list[0].kwargs["timeout"], 3)

        urlopen_mock.side_effect = [
            telegram_response(
                {
                    "ok": True,
                    "result": [
                        {"update_id": 1, "message": {"chat": {"id": 999}, "text": f"APPROVE {approval.id}"}},
                        {"update_id": 2, "message": {"chat": {"id": 12345}, "text": f"approve {approval.id}"}},
                        {"update_id": 3, "message": {"chat": {"id": 12345}, "text": f"APPROVE {approval.id} extra"}},
                        {"update_id": 4, "message": {"chat": {"id": 12345}, "text": f"APPROVE {approval.id}"}},
                    ],
                }
            )
        ]
        self.assertEqual(self.service.poll_once(), 1)
        self.assertEqual(self.approved_jobs, ["job-1"])

    @patch("daksh.telegram_approval.urlopen")
    def test_expired_approval_is_never_started(self, urlopen_mock):
        urlopen_mock.return_value = telegram_response({"ok": True, "result": {"message_id": 1}})
        approval = self.service.request_approval("job-2", "Do not start")
        state = self.service._load()
        state["approvals"][approval.id]["expires_at"] = 0
        self.service._save(state)

        urlopen_mock.return_value = telegram_response(
            {"ok": True, "result": [{"update_id": 1, "message": {"chat": {"id": 12345}, "text": f"APPROVE {approval.id}"}}]}
        )
        self.assertEqual(self.service.poll_once(), 0)
        self.assertEqual(self.approved_jobs, [])
        self.assertEqual(self.service._load()["approvals"][approval.id]["status"], "expired")

    def test_missing_configuration_is_explicit(self):
        service = TelegramApprovalService(
            bot_token=None, allowed_chat_id=None, data_directory=TEST_DATA, on_approved=lambda _: None
        )
        with self.assertRaisesRegex(TelegramApprovalError, "TELEGRAM_BOT_TOKEN"):
            service.request_approval("job", "prompt")


class OpenCodeApprovalGateTests(unittest.TestCase):
    @patch("daksh.opencode_agent.shutil.which", return_value="/usr/local/bin/tool")
    @patch("daksh.opencode_agent.subprocess.run")
    def test_pending_job_does_not_run_until_approved(self, run, _which):
        run.return_value = __import__("subprocess").CompletedProcess(["ollama"], 0, "", "")
        agent = OpenCodeAgent(ROOT, timeout_seconds=5, max_output_bytes=1024)
        job = agent.create_pending("Wait for Telegram")
        self.assertEqual(job.state, "pending_approval")
        self.assertEqual(run.call_count, 1)  # Dependency probe only.
        self.assertTrue(agent.approve(job.id))
        agent._executor.shutdown(wait=True)
        self.assertEqual(job.state, "completed")
        self.assertEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
