"""Unit tests for individual testing and debugging of Document Parser and Wiki Generator return points."""

import pytest
from pathlib import Path
from backend.app.core.ingestion.parser import parse_document_bytes
from backend.app.core.ingestion.wiki_generator import generate_wiki_pages_from_text


def test_parser_return_structure():
    """Verify Document Parser return dictionary schema and keys."""
    sample_text = "WikiLLM Intelligent Knowledge Management System\nPage 1 Content."
    file_bytes = sample_text.encode("utf-8")
    
    parsed = parse_document_bytes(file_bytes, filename="test_doc.txt")
    
    assert isinstance(parsed, dict)
    assert "filename" in parsed
    assert "total_pages" in parsed
    assert "pages" in parsed
    assert "full_text" in parsed
    assert parsed["filename"] == "test_doc.txt"
    assert parsed["total_pages"] == 1
    assert parsed["full_text"] == sample_text


def test_wiki_generator_return_structure(tmp_path):
    """Verify Wiki Generator return list schema, entity dicts, and generated files."""
    user_wiki_dir = tmp_path / "wiki" / "users" / "test_user"
    sample_text = "Tesla Inc is an electric vehicle company founded by Elon Musk in 2003."
    
    pages = generate_wiki_pages_from_text(
        cleaned_text=sample_text,
        filename="company_info.txt",
        wiki_dir=str(user_wiki_dir)
    )
    
    assert isinstance(pages, list)
    assert len(pages) > 0
    
    page = pages[0]
    assert "entity_name" in page
    assert "entity_type" in page
    assert "content" in page
    assert "path" in page
    assert user_wiki_dir.exists()
    assert (user_wiki_dir / "index.json").exists()
    assert (user_wiki_dir / "graph.json").exists()
