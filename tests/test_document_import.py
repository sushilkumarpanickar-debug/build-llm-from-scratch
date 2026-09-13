import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from daksh.document_import import DocumentImportError, DocumentImporter
from rag.knowledge_graph import KnowledgeGraph


class DocumentImporterTests(unittest.TestCase):
    def setUp(self):
        self.importer = DocumentImporter(1024 * 1024)

    def test_imports_utf8_text_with_safe_source_name(self):
        document = self.importer.import_bytes("../plan.md", b"# Plan\nUse local Ollama.")
        self.assertEqual(document.title, "plan")
        self.assertEqual(document.source, "uploaded:plan.md")
        self.assertIn("local Ollama", document.content)

    def test_imports_docx_text_without_evaluating_content(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr(
                "word/document.xml",
                '<w:document xmlns:w="urn:test"><w:body><w:p><w:r><w:t>Private text</w:t></w:r></w:p></w:body></w:document>',
            )
        document = self.importer.import_bytes("notes.docx", stream.getvalue())
        self.assertEqual(document.content, "Private text")

    def test_rejects_unsupported_and_oversized_files(self):
        with self.assertRaisesRegex(DocumentImportError, "Supported formats"):
            self.importer.import_bytes("unsafe.exe", b"content")
        with self.assertRaisesRegex(DocumentImportError, "upload limit"):
            DocumentImporter(3).import_bytes("notes.txt", b"long")

    def test_graph_deduplicates_identical_document_content(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = KnowledgeGraph(Path(directory) / "knowledge_graph.json")
            original = graph.add_document("One", "Same private content", "uploaded:one.txt")
            duplicate = graph.add_document("Two", "Same private content", "uploaded:two.txt")
            self.assertEqual(original.id, duplicate.id)
            self.assertEqual(len(graph.list_documents()), 1)


class DocumentImportAPITests(unittest.TestCase):
    def test_imports_upload_into_an_isolated_graph(self):
        with tempfile.TemporaryDirectory() as directory:
            from unittest.mock import patch
            from daksh.web_dashboard import create_daksh_dashboard

            with patch("daksh.web_dashboard.DAKSH_DATA_DIR", Path(directory)):
                app = create_daksh_dashboard(start_telegram_polling=False)
                response = app.test_client().post(
                    "/api/brain/import",
                    data={"document": (io.BytesIO(b"DAKSH runs locally."), "assistant.txt")},
                    content_type="multipart/form-data",
                )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.get_json()["source"], "uploaded:assistant.txt")

    def test_lists_and_executes_only_registered_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            from unittest.mock import patch
            from daksh.web_dashboard import create_daksh_dashboard

            with patch("daksh.web_dashboard.DAKSH_DATA_DIR", Path(directory)):
                app = create_daksh_dashboard(start_telegram_polling=False)
                client = app.test_client()
                registry = client.get("/api/skills").get_json()["skills"]
                self.assertEqual({item["slug"] for item in registry}, {
                    "text-processing", "data-analysis", "synthesis",
                })
                response = client.post(
                    "/api/skills",
                    json={"skill": "text-processing", "input": {"text": " One   two "}},
                )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["final_output"]["cleaned_text"], "One two")


if __name__ == "__main__":
    unittest.main()
