import io
import hashlib
import hmac
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from openpyxl import Workbook

from local_workspace import communications, finance, finance_mcp, ingestion
from local_workspace.server import TOKEN, create_app


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.temp.name))
        self.client = TestClient(self.app, base_url="http://127.0.0.1")
        self.headers = {"X-Workspace-Token": TOKEN}
        self.models_patch = patch("local_workspace.server.ollama_client.models", return_value=["qwen-test", "nomic-embed-text:latest"])
        self.chat_models_patch = patch("local_workspace.server.ollama_client.chat_models", return_value=["qwen-test"])
        self.models_patch.start()
        self.chat_models_patch.start()

    def tearDown(self):
        self.client.close()
        self.models_patch.stop()
        self.chat_models_patch.stop()
        self.temp.cleanup()

    def post(self, path, data):
        return self.client.post(path, json=data, headers=self.headers)

    def test_assets_health_and_host_protection(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("AI CORE OVERVIEW", page.text)
        self.assertIn("LIVE INTELLIGENCE FEED", page.text)
        self.assertIn("MISSION TIMELINE", page.text)
        self.assertIn("START VOICE SESSION", page.text)
        self.assertIn("DAKSH VOICE LINK", page.text)
        self.assertIn("COGNITIVE CORE", page.text)
        self.assertIn("FINANCE INTELLIGENCE", page.text)
        self.assertIn("MCP &amp; CONNECTOR CONTROL PLANE", page.text)
        self.assertIn("COMMUNICATIONS BRIDGE", page.text)
        self.assertIn("APPROVAL QUEUE", page.text)
        self.assertEqual(self.client.get("/snns_logo.png").content[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(self.client.get("/snns_emblem.png").content[:8], b"\x89PNG\r\n\x1a\n")
        self.assertTrue(self.client.get("/api/health").json()["local_only"])
        self.assertEqual(self.client.get("/api/state", headers={"Host": "evil.example"}).status_code, 403)

    def test_communications_intake_approval_and_task_staging(self):
        state = self.client.get("/api/state").json()
        self.assertEqual(state["communications"]["pending_approvals"], 0)
        checked = self.post("/api/communications/poll", {"scope": "Personal"})
        self.assertEqual(checked.status_code, 200)
        self.assertTrue(all(item.get("skipped") for item in checked.json()["results"]))

        payload = {
            "entry": [{"changes": [{"value": {
                "contacts": [{"wa_id": "919900001111", "profile": {"name": "Owner"}}],
                "messages": [{
                    "id": "wamid.test-1", "from": "919900001111", "timestamp": "1789320000",
                    "type": "text", "text": {"body": "/daksh prepare the cash report"},
                }],
            }}]}],
        }
        body = json.dumps(payload, separators=(",", ":")).encode()
        secret = "test-app-secret"
        signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        connector_env = {
            "DAKSH_WHATSAPP_VERIFY_TOKEN": "verify-me",
            "DAKSH_WHATSAPP_APP_SECRET": secret,
            "DAKSH_WHATSAPP_ALLOWED_NUMBERS": "919900001111",
        }
        with patch.dict("os.environ", connector_env, clear=False):
            verified = self.client.get(
                "/api/webhooks/whatsapp",
                params={"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "accepted"},
            )
            self.assertEqual(verified.text, "accepted")
            rejected = self.client.post("/api/webhooks/whatsapp", content=body)
            self.assertEqual(rejected.status_code, 403)
            received = self.client.post(
                "/api/webhooks/whatsapp", content=body,
                headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature},
            )
        self.assertEqual(received.status_code, 200, received.text)
        comm = self.client.get("/api/communications?scope=Personal").json()
        self.assertEqual(comm["unread_messages"], 1)
        self.assertEqual(comm["pending_approvals"], 1)
        approval_id = comm["approvals"][0]["id"]
        approved = self.post(f"/api/communications/approvals/{approval_id}", {"scope": "Personal", "status": "approved"})
        self.assertEqual(approved.status_code, 200, approved.text)
        state = self.client.get("/api/state?scope=Personal").json()
        self.assertEqual(state["communications"]["pending_approvals"], 0)
        self.assertEqual(state["communications"]["inbox"][0]["status"], "staged")
        self.assertIn("prepare the cash report", state["tasks"][0]["plan"])

    def test_memory_is_explicit_categorized_and_scoped(self):
        response = self.post("/api/memories", {
            "scope": "Personal", "title": "Output style", "content": "Prefer concise reports",
            "source": "User", "category": "preferences",
        })
        self.assertEqual(response.status_code, 200)
        personal = self.client.get("/api/state?scope=Personal").json()
        snns = self.client.get("/api/state?scope=SNNS%20Smartact").json()
        self.assertEqual(personal["notes"][0]["category"], "preferences")
        self.assertEqual(snns["notes"], [])
        blocked = self.post("/api/memories", {
            "title": "Secret", "content": "My OTP is 123456", "source": "User", "category": "preferences"
        })
        self.assertEqual(blocked.status_code, 400)

    def test_conversations_and_explicit_remember(self):
        created = self.post("/api/conversations", {"title": "Planning"}).json()
        response = self.post("/api/chat", {
            "prompt": "Remember that board reports should be concise", "conversation_id": created["id"], "model": "qwen-test"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Saved as", response.json()["response"])
        state = self.client.get(f"/api/state?conversation_id={created['id']}").json()
        self.assertEqual(len(state["messages"]), 2)
        self.assertEqual(len(state["notes"]), 1)
        deleted = self.client.delete(f"/api/conversations/{created['id']}?scope=Personal", headers=self.headers)
        self.assertEqual(deleted.status_code, 200)

    def test_document_index_and_semantic_retrieval(self):
        def fake_embed(texts, _model="nomic-embed-text"):
            values = [texts] if isinstance(texts, str) else texts
            return [[1.0, float("dispatch" in value.lower())] for value in values]

        with patch("local_workspace.ingestion.ollama_client.embed", side_effect=fake_embed):
            response = self.client.post(
                "/api/documents", headers=self.headers, data={"scope": "Personal"},
                files={"file": ("operations.txt", b"Coal dispatch target is 12000 tonnes this week.", "text/plain")},
            )
            self.assertEqual(response.status_code, 200, response.text)
            document = response.json()["document"]
            self.assertEqual(document["chunk_count"], 1)
            results = ingestion.retrieve(self.app.state.store, "Personal", "dispatch", limit=1)
            self.assertEqual(results[0]["filename"], "operations.txt")

    def test_grounded_chat_persists_sources(self):
        store = self.app.state.store
        document_id, _ = store.execute(
            "INSERT INTO documents(scope,filename,stored_name,sha256,kind,status,chunk_count,created) VALUES(?,?,?,?,?,'ready',1,?)",
            ("Personal", "facts.txt", "facts.txt", "sha", "txt", "2026-09-13T00:00:00+00:00"),
        )
        store.execute(
            "INSERT INTO chunks(document_id,scope,content,metadata,embedding) VALUES(?,?,?,?,?)",
            (document_id, "Personal", "The answer is 42.", '{"filename":"facts.txt","location":"document","chunk":1}', "[1.0,0.0]"),
        )
        conversation = self.client.get("/api/state").json()["conversation"]
        with patch("local_workspace.server.ingestion.retrieve", return_value=[{
            "id":1,"document_id":document_id,"content":"The answer is 42.","filename":"facts.txt",
            "location":"document","chunk":1,"score":0.9,
        }]), patch("local_workspace.server.ollama_client.chat", return_value="It is 42. [Source: facts.txt — document]"):
            response = self.post("/api/chat", {"prompt":"What is the answer?","model":"qwen-test","conversation_id":conversation["id"]})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["sources"][0]["title"], "facts.txt")
        messages = self.client.get(f"/api/state?conversation_id={conversation['id']}").json()["messages"]
        self.assertEqual(messages[-1]["sources"][0]["title"], "facts.txt")

    def test_voice_chat_uses_concise_conversational_prompt(self):
        conversation = self.client.get("/api/state").json()["conversation"]
        captured = {}

        def fake_chat(_model, messages):
            captured["system"] = messages[0]["content"]
            return "I am listening. What shall we work on?"

        with patch("local_workspace.server.ollama_client.chat", side_effect=fake_chat):
            response = self.post("/api/chat", {
                "prompt": "Hello DAKSH", "model": "qwen-test",
                "conversation_id": conversation["id"], "voice_mode": True, "speak": False,
            })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("spoken conversation", captured["system"])
        self.assertIn("one to four short sentences", captured["system"])

    def test_settings_task_and_write_token(self):
        self.assertEqual(self.client.post("/api/settings", json={"model":"qwen-test"}).status_code, 403)
        saved = self.post("/api/settings", {"model":"qwen-test","stt_model":"tiny","speech_enabled":"true"})
        self.assertEqual(saved.status_code, 200)
        with patch("local_workspace.server.ollama_client.chat", return_value="1. Inspect\n2. Deliver"):
            task = self.post("/api/tasks", {"prompt":"Plan the report","model":"qwen-test"})
        self.assertEqual(task.status_code, 200)
        status = self.post("/api/tasks/status", {"id":task.json()["id"],"status":"completed"})
        self.assertEqual(status.status_code, 200)

    def test_finance_analysis_and_connector_catalog(self):
        csv_data = b"Date,Sales,Expense,Balance\n2026-09-01,1000,400,600\n2026-09-02,1250,500,1350\n"
        response = self.client.post(
            "/api/finance/analyze", headers=self.headers, data={"scope": "Tiwarta CFO"},
            files={"file": ("ledger.csv", csv_data, "text/csv")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        columns = {item["name"]: item for item in response.json()["sheets"][0]["numeric_columns"]}
        self.assertEqual(columns["Sales"]["sum"], 2250.0)
        self.assertEqual(columns["Expense"]["role"], "outflow")
        catalog = self.client.get("/api/integrations").json()
        self.assertFalse(catalog["auto_install"])
        self.assertEqual(catalog["integrations"][0]["id"], "daksh-finance")
        decisions = {item["id"]: item["decision"] for item in catalog["integrations"]}
        self.assertEqual(decisions["codebase-memory"], "built_now")
        self.assertEqual(decisions["parallel-search"], "optional")
        self.assertEqual(decisions["rememble"], "overlap")

    def test_finance_xlsx_and_mcp_allowlist(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Cash Flow"
        sheet.append(["Month", "Collections", "Payments"])
        sheet.append(["September", 5000, 3200])
        payload = io.BytesIO()
        workbook.save(payload)
        result = finance.analyze_bytes("cash-flow.xlsx", payload.getvalue())
        self.assertEqual(result["sheets"][0]["numeric_columns"][0]["sum"], 5000.0)
        self.assertEqual(result["sheets"][0]["numeric_columns"][0]["role"], "inflow")
        root = Path(self.temp.name) / "finance"
        root.mkdir()
        source = root / "ledger.csv"
        source.write_text("Debit,Credit\n50,75\n", encoding="utf-8")
        message = {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "finance_analyze_file", "arguments": {"path": str(source)}}}
        mcp_result = finance_mcp.handle(message, root)
        self.assertFalse(mcp_result["result"]["isError"])
        blocked = finance_mcp.handle({**message, "params": {"name": "finance_analyze_file", "arguments": {"path": __file__}}}, root)
        self.assertTrue(blocked["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
