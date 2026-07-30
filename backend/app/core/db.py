"""Database core module providing SQLite/PostgreSQL database connections, schema initialization, and transactional operations for WikiMind."""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from .paths import get_project_root, get_user_wiki_dir


from .config import get_settings

try:
    import libsql_client
except ImportError:
    libsql_client = None


class TursoRow(dict):
    """Dictionary subclass supporting index access to mimic sqlite3.Row."""
    def __init__(self, cols, vals):
        super().__init__(zip(cols, vals))
        self._vals = tuple(vals)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._vals[key]
        return super().__getitem__(key)


class TursoCursor:
    """Cursor wrapper for libsql_client to provide a sqlite3-compatible interface."""
    def __init__(self, client):
        self.client = client
        self._results = []
        self._idx = 0

    def execute(self, stmt: str, params: tuple = ()):
        p = list(params) if isinstance(params, (tuple, list)) else params
        rs = self.client.execute(stmt, p)
        cols = getattr(rs, 'columns', [])
        rows = getattr(rs, 'rows', [])
        self._results = [TursoRow(cols, list(r)) for r in rows]
        self._idx = 0
        return self

    def executescript(self, script: str):
        stmts = [s.strip() for s in script.split(';') if s.strip()]
        for stmt in stmts:
            self.client.execute(stmt)
        return self

    def fetchone(self):
        if self._idx < len(self._results):
            row = self._results[self._idx]
            self._idx += 1
            return row
        return None

    def fetchall(self):
        res = self._results[self._idx:]
        self._idx = len(self._results)
        return res


class TursoConnection:
    """Connection wrapper for libsql_client."""
    def __init__(self, client):
        self.client = client

    def cursor(self):
        return TursoCursor(self.client)

    def commit(self):
        pass

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass


def get_db_path() -> Path:
    """Get absolute path to local SQLite database file inside storage directory."""
    storage_dir = get_project_root() / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / "wikimind.db"


def get_db_connection():
    """Get database connection (Turso cloud SQLite if configured, otherwise local SQLite)."""
    settings = get_settings()
    turso_url = os.environ.get("TURSO_DATABASE_URL") or settings.turso_database_url
    turso_token = os.environ.get("TURSO_AUTH_TOKEN") or settings.turso_auth_token

    if libsql_client and turso_url and turso_token:
        url = turso_url
        if url.startswith("libsql://"):
            url = url.replace("libsql://", "https://", 1)
        client = libsql_client.create_client_sync(url, auth_token=turso_token)
        return TursoConnection(client)

    conn = sqlite3.connect(get_db_path(), timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables for wiki_pages, wiki_graph_edges, and raw_documents."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS wiki_pages (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            entity_name TEXT NOT NULL,
            entity_type TEXT NOT NULL DEFAULT 'CONCEPT',
            filename TEXT,
            content_md TEXT NOT NULL,
            summary TEXT,
            category TEXT,
            tags TEXT,
            related_entities TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_wiki_pages_user ON wiki_pages(user_id);
        CREATE INDEX IF NOT EXISTS idx_wiki_pages_entity ON wiki_pages(user_id, entity_name);

        CREATE TABLE IF NOT EXISTS wiki_graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            source_entity TEXT NOT NULL,
            relation TEXT NOT NULL,
            target_entity TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_graph_edges_user ON wiki_graph_edges(user_id);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON wiki_graph_edges(user_id, source_entity);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON wiki_graph_edges(user_id, target_entity);

        CREATE TABLE IF NOT EXISTS raw_documents (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            mime_type TEXT,
            size_bytes INTEGER,
            file_bytes BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_raw_docs_user ON raw_documents(user_id);

        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);

        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(user_id, session_id);
    """)

    conn.commit()
    conn.close()


# Ensure DB tables are initialized on import
init_db()


def save_wiki_page_db(
    user_id: str,
    entity_name: str,
    entity_type: str,
    filename: str,
    content_md: str,
    summary: str = "",
    related_entities: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Save or update a Wiki Markdown page in the wiki_pages database table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    page_id = f"{user_id}:{entity_name}"
    now_str = datetime.now().isoformat()
    related_json = json.dumps(related_entities or [])

    cursor.execute("""
        INSERT INTO wiki_pages (id, user_id, entity_name, entity_type, filename, content_md, summary, related_entities, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            content_md = excluded.content_md,
            entity_type = excluded.entity_type,
            filename = excluded.filename,
            summary = excluded.summary,
            related_entities = excluded.related_entities,
            updated_at = excluded.updated_at
    """, (page_id, user_id, entity_name, entity_type, filename, content_md, summary, related_json, now_str, now_str))

    conn.commit()
    conn.close()

    return {
        "id": page_id,
        "user_id": user_id,
        "entity_name": entity_name,
        "entity_type": entity_type,
        "filename": filename,
        "content_md": content_md,
        "updated_at": now_str
    }


def get_wiki_page_db(user_id: str, entity_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve a Wiki page record from database by user_id and entity_name."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM wiki_pages WHERE user_id = ? AND entity_name = ?
    """, (user_id, entity_name))
    row = cursor.fetchone()
    conn.close()

    if row:
        res = dict(row)
        res["related_entities"] = json.loads(res.get("related_entities") or "[]")
        return res
    return None


def get_user_wiki_pages_db(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all Wiki pages for a specific user from database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM wiki_pages WHERE user_id = ? ORDER BY entity_name ASC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    pages = []
    for r in rows:
        d = dict(r)
        d["related_entities"] = json.loads(d.get("related_entities") or "[]")
        pages.append(d)
    return pages


def save_graph_edges_db(user_id: str, relationships: List[Dict[str, Any]]) -> int:
    """Save graph relationship edges into wiki_graph_edges database table."""
    if not relationships:
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    count = 0
    now_str = datetime.now().isoformat()
    for rel in relationships:
        src = rel.get("source", "").strip()
        r_type = rel.get("relation", "RELATED_TO").strip()
        tgt = rel.get("target", "").strip()

        if src and tgt:
            # Avoid duplicate identical edges
            cursor.execute("""
                SELECT id FROM wiki_graph_edges WHERE user_id = ? AND source_entity = ? AND relation = ? AND target_entity = ?
            """, (user_id, src, r_type, tgt))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO wiki_graph_edges (user_id, source_entity, relation, target_entity, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, src, r_type, tgt, now_str))
                count += 1

    conn.commit()
    conn.close()
    return count


def get_user_graph_edges_db(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all graph relationship edges for a user from database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT source_entity as source, relation, target_entity as target FROM wiki_graph_edges WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]



def save_chat_message_db(
    user_id: str,
    session_id: str,
    role: str,
    content: str,
    sources: Optional[List[Dict[str, Any]]] = None,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Save a chat message and update/create the parent chat session in database."""
    import uuid
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    msg_id = str(uuid.uuid4())

    # Ensure session exists or create it
    cursor.execute("""
        SELECT title FROM chat_sessions WHERE user_id = ? AND id = ?
    """, (user_id, session_id))
    session_row = cursor.fetchone()

    if not session_row:
        sess_title = title or (content[:35] + '...' if len(content) > 35 else content) or "New Chat"
        cursor.execute("""
            INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user_id, sess_title, now_str, now_str))
    else:
        cursor.execute("""
            UPDATE chat_sessions SET updated_at = ? WHERE user_id = ? AND id = ?
        """, (now_str, user_id, session_id))

    # Insert message
    sources_json = json.dumps(sources or [])
    cursor.execute("""
        INSERT INTO chat_messages (id, session_id, user_id, role, content, sources, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (msg_id, session_id, user_id, role, content, sources_json, now_str))

    conn.commit()
    conn.close()

    return {
        "id": msg_id,
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "sources": sources or [],
        "created_at": now_str
    }


def get_user_chat_sessions_db(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all chat sessions for a user ordered by last update."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, title, created_at, updated_at 
        FROM chat_sessions 
        WHERE user_id = ? 
        ORDER BY updated_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


def get_session_messages_db(user_id: str, session_id: str) -> List[Dict[str, Any]]:
    """Retrieve all messages for a specific chat session."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, session_id, user_id, role, content, sources, created_at 
        FROM chat_messages 
        WHERE user_id = ? AND session_id = ? 
        ORDER BY created_at ASC
    """, (user_id, session_id))
    rows = cursor.fetchall()
    conn.close()

    messages = []
    for r in rows:
        d = dict(r)
        d["sources"] = json.loads(d.get("sources") or "[]")
        messages.append(d)
    return messages


def delete_chat_session_db(user_id: str, session_id: str) -> bool:
    """Delete a chat session and all its messages."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chat_messages WHERE user_id = ? AND session_id = ?", (user_id, session_id))
    cursor.execute("DELETE FROM chat_sessions WHERE user_id = ? AND id = ?", (user_id, session_id))

    conn.commit()
    conn.close()
    return True

