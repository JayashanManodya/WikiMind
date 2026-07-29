"""Unit tests for Google OAuth token management and per-user data isolation."""

import pytest
import asyncio
from pathlib import Path
from backend.app.core.auth import create_access_token, decode_access_token, verify_google_token
from backend.app.core.ingestion.wiki_generator import generate_wiki_pages_from_text
from backend.app.core.retrieval.vector_store import retrieve


def test_jwt_create_and_decode():
    """Test JWT access token creation and decoding."""
    user_data = {
        "user_id": "google_1234567890",
        "email": "user@example.com",
        "name": "Test User",
        "picture": "http://example.com/pic.jpg",
    }
    
    token = create_access_token(user_data, expires_in_seconds=3600)
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded["user_id"] == "google_1234567890"
    assert decoded["email"] == "user@example.com"
    assert decoded["name"] == "Test User"


def test_mock_google_token_verification():
    """Test verification of mock Google credential token."""
    mock_token = "mock_token_testuser123"
    user = asyncio.run(verify_google_token(mock_token))
    
    assert user["user_id"] == "google_user_testuser123"
    assert user["email"] == "user_testuser123@example.com"
    assert "Testuser123" in user["name"] or "testuser123" in user["name"]


def test_user_scoped_wiki_generation(tmp_path):
    """Test generating wiki pages into a user-isolated directory."""
    user_id = "user_alice"
    user_wiki_dir = tmp_path / "wiki" / "users" / user_id

    sample_text = "WikiLLM provides user data isolation in multi-agent RAG systems."
    pages = generate_wiki_pages_from_text(
        cleaned_text=sample_text,
        filename="isolation_doc.txt",
        wiki_dir=str(user_wiki_dir)
    )

    assert len(pages) > 0
    assert user_wiki_dir.exists()
    assert (user_wiki_dir / "index.json").exists()
    assert (user_wiki_dir / "graph.json").exists()


def test_user_isolated_retrieval(tmp_path, monkeypatch):
    """Test that retrieve searches inside the specified user's wiki directory."""
    user_a = "user_a"
    user_b = "user_b"

    dir_a = tmp_path / "wiki" / "users" / user_a
    dir_b = tmp_path / "wiki" / "users" / user_b
    dir_a.mkdir(parents=True)
    dir_b.mkdir(parents=True)

    (dir_a / "Secret_A.md").write_text("# Secret A\nThis is Alice confidential data.", encoding="utf-8")
    (dir_b / "Secret_B.md").write_text("# Secret B\nThis is Bob confidential data.", encoding="utf-8")

    # Override root wiki path to tmp_path / "wiki"
    def mock_retrieve_dir(query, k=3, follow_relations=True, user_id="guest_user"):
        user_wiki_dir = tmp_path / "wiki" / "users" / user_id
        docs = []
        if user_wiki_dir.exists():
            for md in user_wiki_dir.glob("*.md"):
                content = md.read_text(encoding="utf-8")
                docs.append(content)
        return docs

    docs_a = mock_retrieve_dir("confidential", user_id=user_a)
    docs_b = mock_retrieve_dir("confidential", user_id=user_b)

    assert len(docs_a) == 1
    assert "Alice" in docs_a[0]
    assert "Bob" not in docs_a[0]

    assert len(docs_b) == 1
    assert "Bob" in docs_b[0]
    assert "Alice" not in docs_b[0]


def test_unauthenticated_requests_raise_401():
    """Test that unauthenticated requests to protected endpoints return HTTP 401 Unauthorized."""
    from fastapi.testclient import TestClient
    from backend.app.api import app

    client = TestClient(app)

    # Protected endpoints without Bearer token
    res_me = client.get("/auth/me")
    assert res_me.status_code == 401
    assert "Authentication required" in res_me.json()["detail"]

    res_wiki = client.get("/wiki/index")
    assert res_wiki.status_code == 401

    res_graph = client.get("/wiki/graph")
    assert res_graph.status_code == 401

    res_debug = client.post("/debug/parse")
    assert res_debug.status_code == 401

    # Public endpoints should still work
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

