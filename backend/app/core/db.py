"""Database core module providing SQLite/PostgreSQL database connections, schema initialization, and transactional operations for WikiMind."""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from .paths import get_project_root, get_user_wiki_dir


def get_db_path() -> Path:
    """Get absolute path to local SQLite database file inside storage directory."""
    storage_dir = get_project_root() / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / "wikimind.db"


def get_db_connection() -> sqlite3.Connection:
    """Get SQLite database connection with row factory enabled."""
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
