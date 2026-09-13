"""Safe local text extraction for documents added to the DAKSH second brain."""

from __future__ import annotations

import io
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import PurePath
from xml.etree import ElementTree

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class DocumentImportError(ValueError):
    """Raised for malformed, unsupported, or oversized imported documents."""


@dataclass(frozen=True)
class ImportedDocument:
    title: str
    content: str
    source: str


class DocumentImporter:
    """Extract supported files without evaluating their contents or macros."""

    _TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json"}
    _SUPPORTED_EXTENSIONS = _TEXT_EXTENSIONS | {".docx", ".pdf"}

    def __init__(self, max_bytes: int) -> None:
        if max_bytes < 1:
            raise ValueError("Document size limit must be positive.")
        self.max_bytes = max_bytes

    def import_bytes(self, filename: str, content: bytes) -> ImportedDocument:
        safe_name = self._safe_name(filename)
        if not content:
            raise DocumentImportError("The uploaded document is empty.")
        if len(content) > self.max_bytes:
            raise DocumentImportError(
                f"The document exceeds the {self.max_bytes // (1024 * 1024)} MB upload limit."
            )
        extension = PurePath(safe_name).suffix.lower()
        if extension not in self._SUPPORTED_EXTENSIONS:
            raise DocumentImportError("Supported formats: TXT, Markdown, CSV, JSON, DOCX, and PDF.")
        if extension in self._TEXT_EXTENSIONS:
            extracted = self._decode_text(content, safe_name)
        elif extension == ".docx":
            extracted = self._extract_docx(content)
        else:
            extracted = self._extract_pdf(content)
        extracted = self._normalize(extracted)
        if not extracted:
            raise DocumentImportError("No readable text was found in the uploaded document.")
        return ImportedDocument(
            title=PurePath(safe_name).stem[:200] or "Imported document",
            content=extracted,
            source=f"uploaded:{safe_name}",
        )

    @staticmethod
    def _safe_name(filename: str) -> str:
        name = PurePath(filename).name.strip()
        if not name or name in {".", ".."}:
            raise DocumentImportError("A valid document filename is required.")
        return re.sub(r"[^A-Za-z0-9._ -]", "_", name)[:255]

    @staticmethod
    def _decode_text(content: bytes, filename: str) -> str:
        try:
            return content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise DocumentImportError(f"{filename} must use UTF-8 text encoding.") from error

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                document = archive.read("word/document.xml")
            root = ElementTree.fromstring(document)
        except (KeyError, zipfile.BadZipFile, ElementTree.ParseError) as error:
            raise DocumentImportError("The DOCX file is corrupt or unsupported.") from error
        return "\n".join(
            "".join(node.itertext()).strip()
            for node in root.iter()
            if node.tag.endswith("}p") and "".join(node.itertext()).strip()
        )

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except (PdfReadError, ValueError, OSError) as error:
            raise DocumentImportError("The PDF could not be read as text.") from error

    @staticmethod
    def _normalize(content: str) -> str:
        return "\n".join(line.strip() for line in content.splitlines() if line.strip())[:100_000]
