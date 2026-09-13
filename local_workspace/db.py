import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCOPES = ("Personal", "CA Professional", "Tiwarta CFO", "SNNS Smartact")
MEMORY_CATEGORIES = (
    "preferences", "companies", "contacts", "projects",
    "commercial_assumptions", "standard_formats", "business_rules",
)


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir or os.environ.get("DAKSH_DATA_DIR", ROOT / "data"))
        self.db_path = self.data_dir / "workspace.sqlite3"
        self.documents_dir = self.data_dir / "documents"

    def connect(self):
        con = sqlite3.connect(self.db_path, timeout=15, check_same_thread=False)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def initialize(self):
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.documents_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS notes(
              id INTEGER PRIMARY KEY, scope TEXT NOT NULL, title TEXT NOT NULL,
              content TEXT NOT NULL, source TEXT NOT NULL, created TEXT NOT NULL,
              category TEXT NOT NULL DEFAULT 'business_rules'
            );
            CREATE TABLE IF NOT EXISTS conversations(
              id INTEGER PRIMARY KEY, scope TEXT NOT NULL, title TEXT NOT NULL,
              created TEXT NOT NULL, updated TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages(
              id INTEGER PRIMARY KEY, scope TEXT NOT NULL, role TEXT NOT NULL,
              content TEXT NOT NULL, created TEXT NOT NULL,
              conversation_id INTEGER, sources TEXT NOT NULL DEFAULT '[]',
              FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS tasks(
              id INTEGER PRIMARY KEY, scope TEXT NOT NULL, title TEXT NOT NULL,
              status TEXT NOT NULL, plan TEXT NOT NULL, created TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS documents(
              id INTEGER PRIMARY KEY, scope TEXT NOT NULL, filename TEXT NOT NULL,
              stored_name TEXT NOT NULL, sha256 TEXT NOT NULL, kind TEXT NOT NULL,
              status TEXT NOT NULL, chunk_count INTEGER NOT NULL DEFAULT 0,
              created TEXT NOT NULL, UNIQUE(scope, sha256)
            );
            CREATE TABLE IF NOT EXISTS chunks(
              id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL, scope TEXT NOT NULL,
              content TEXT NOT NULL, metadata TEXT NOT NULL, embedding TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS settings(
              scope TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
              updated TEXT NOT NULL, PRIMARY KEY(scope, key)
            );
            CREATE TABLE IF NOT EXISTS audit_log(
              id INTEGER PRIMARY KEY, scope TEXT NOT NULL, event TEXT NOT NULL,
              detail TEXT NOT NULL, created TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS notes_scope ON notes(scope);
            CREATE INDEX IF NOT EXISTS conversations_scope ON conversations(scope, updated DESC);
            CREATE INDEX IF NOT EXISTS tasks_scope ON tasks(scope);
            CREATE INDEX IF NOT EXISTS documents_scope ON documents(scope, id DESC);
            CREATE INDEX IF NOT EXISTS chunks_scope ON chunks(scope);
            """)
            self._add_column(con, "notes", "category", "TEXT NOT NULL DEFAULT 'business_rules'")
            self._add_column(con, "messages", "conversation_id", "INTEGER")
            self._add_column(con, "messages", "sources", "TEXT NOT NULL DEFAULT '[]'")
            con.execute("CREATE INDEX IF NOT EXISTS messages_conversation ON messages(conversation_id, id)")
            for scope in SCOPES:
                row = con.execute("SELECT id FROM conversations WHERE scope=? ORDER BY id LIMIT 1", (scope,)).fetchone()
                if row is None:
                    cur = con.execute(
                        "INSERT INTO conversations(scope,title,created,updated) VALUES(?,?,?,?)",
                        (scope, "First conversation", utcnow(), utcnow()),
                    )
                    conversation_id = cur.lastrowid
                else:
                    conversation_id = row["id"]
                con.execute(
                    "UPDATE messages SET conversation_id=? WHERE scope=? AND conversation_id IS NULL",
                    (conversation_id, scope),
                )
        os.chmod(self.db_path, 0o600)

    @staticmethod
    def _add_column(con, table, column, declaration):
        columns = {row["name"] for row in con.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")

    def rows(self, query, params=()):
        with self.connect() as con:
            return [dict(row) for row in con.execute(query, params)]

    def execute(self, query, params=()):
        with self.connect() as con:
            cur = con.execute(query, params)
            return cur.lastrowid, cur.rowcount

    def setting(self, scope, key, default=None):
        rows = self.rows("SELECT value FROM settings WHERE scope=? AND key=?", (scope, key))
        return rows[0]["value"] if rows else default

    def set_setting(self, scope, key, value):
        self.execute(
            "INSERT INTO settings(scope,key,value,updated) VALUES(?,?,?,?) "
            "ON CONFLICT(scope,key) DO UPDATE SET value=excluded.value,updated=excluded.updated",
            (scope, key, str(value), utcnow()),
        )

    def audit(self, scope, event, detail):
        self.execute(
            "INSERT INTO audit_log(scope,event,detail,created) VALUES(?,?,?,?)",
            (scope, event, detail[:1000], utcnow()),
        )

    def conversation(self, scope, conversation_id=None):
        with self.connect() as con:
            if conversation_id is not None:
                row = con.execute(
                    "SELECT * FROM conversations WHERE id=? AND scope=?", (conversation_id, scope)
                ).fetchone()
                if row:
                    return dict(row)
            row = con.execute(
                "SELECT * FROM conversations WHERE scope=? ORDER BY updated DESC,id DESC LIMIT 1", (scope,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def decode_json(value, default):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return default
