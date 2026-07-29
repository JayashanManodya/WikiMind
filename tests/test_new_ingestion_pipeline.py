"""Unit and integration tests for the 8-stage WikiLLM Ingestion Pipeline."""

import os
import json
import pytest
from pathlib import Path

from backend.app.core.ingestion.raw_storage import store_raw_document
from backend.app.core.ingestion.llama_parser import parse_with_llamaparse_or_fallback
from backend.app.core.ingestion.cleaner import clean_and_normalize_markdown
from backend.app.core.ingestion.enricher import enrich_document
from backend.app.core.ingestion.extractor import extract_structured_knowledge
from backend.app.core.ingestion.wiki_engine import update_or_create_wiki_pages
from backend.app.core.ingestion.index_manager import update_wiki_index_catalog
from backend.app.core.ingestion.logger_manager import append_ingestion_log
from backend.app.core.ingestion.wiki_generator import run_ingestion_pipeline


def test_stage1_raw_document_storage(tmp_path):
    """Test Stage 1: Immutable storage of raw documents."""
    sample_bytes = b"Hello WikiLLM Raw Document Test"
    res = store_raw_document(
        file_bytes=sample_bytes,
        filename="test_doc.pdf",
        user_id="user123",
        base_dir=str(tmp_path / "raw")
    )
    
    assert res["is_immutable"] is True
    assert res["size_bytes"] == len(sample_bytes)
    assert Path(res["immutable_path"]).exists()
    assert Path(res["immutable_path"]).read_bytes() == sample_bytes


def test_stage2_structured_parsing():
    """Test Stage 2: Structured markdown extraction."""
    sample_text = "# Section 1\n\nThis is paragraph content.\n\n| Table Header 1 | Table Header 2 |\n| --- | --- |\n| Val 1 | Val 2 |\n"
    sample_bytes = sample_text.encode("utf-8")

    parsed = parse_with_llamaparse_or_fallback(sample_bytes, "test.md")
    
    assert "filename" in parsed
    assert "total_pages" in parsed
    assert "full_markdown" in parsed
    assert "Section 1" in parsed["full_markdown"]


def test_stage3_cleaner_and_normalizer():
    """Test Stage 3: Cleaning and normalization."""
    raw_md = """Page 1 of 10

# Title    Header

Back to Top

This is a paragraph with bad  spacing and tab\tcontent.

Page 1 of 10

Duplicate paragraph here with long enough text to trigger duplicate check.

Duplicate paragraph here with long enough text to trigger duplicate check.

# Title    Header
"""
    parsed = {"full_markdown": raw_md, "filename": "test.md", "total_pages": 10}
    cleaned = clean_and_normalize_markdown(parsed)

    cleaned_md = cleaned["cleaned_markdown"]
    assert "Page 1 of 10" not in cleaned_md
    assert "Back to Top" not in cleaned_md
    assert "bad spacing" in cleaned_md
    assert cleaned_md.count("Duplicate paragraph here") == 1


def test_stage4_content_enrichment():
    """Test Stage 4: Content enrichment metadata generation."""
    md = "# Artificial Intelligence\n\nArtificial Intelligence (AI) was developed by Alan Turing and computer scientists at Stanford University."
    enrichment = enrich_document(md, "ai_doc.md")

    assert "title" in enrichment
    assert "executive_summary" in enrichment
    assert isinstance(enrichment["concepts"], list)


def test_stage5_knowledge_extraction():
    """Test Stage 5: Knowledge extraction into structured JSON schema."""
    md = "# Tesla Inc\n\nTesla Inc is an electric vehicle company founded by Elon Musk in 2003."
    enrichment = enrich_document(md, "tesla.md")
    
    knowledge = extract_structured_knowledge(md, enrichment, "tesla.md")

    assert "entities" in knowledge
    assert "concepts" in knowledge
    assert "relationships" in knowledge
    assert "facts" in knowledge
    assert "contradictions" in knowledge
    assert isinstance(knowledge["entities"], list)


def test_stage6_stage7_stage8_end_to_end_pipeline(tmp_path):
    """Test Stages 6, 7, and 8 incrementally updating wiki, maintaining index, and logging."""
    user_wiki_dir = tmp_path / "wiki" / "users" / "test_user"

    doc_text = "# OpenAI Systems\n\nOpenAI created ChatGPT and GPT-4 model architecture."
    doc_bytes = doc_text.encode("utf-8")

    res = run_ingestion_pipeline(
        file_bytes=doc_bytes,
        filename="openai_overview.md",
        user_id="test_user",
        wiki_dir=str(user_wiki_dir)
    )

    assert res["status"] == "success"
    assert len(res["wiki_pages"]) > 0
    assert user_wiki_dir.exists()
    
    # Check Index.md
    index_md = user_wiki_dir / "Index.md"
    assert index_md.exists()
    assert "Wiki Knowledge Base Index" in index_md.read_text(encoding="utf-8")

    # Check log.md
    log_md = user_wiki_dir / "log.md"
    assert log_md.exists()
    assert "Ingestion Run: `openai_overview.md`" in log_md.read_text(encoding="utf-8")

    # Re-run second ingestion with conflicting or updated fact to test incremental update & log append
    doc_text_2 = "# OpenAI Systems\n\nOpenAI updated GPT-4 with real-time reasoning capabilities in 2026."
    res2 = run_ingestion_pipeline(
        file_bytes=doc_text_2.encode("utf-8"),
        filename="openai_v2.md",
        user_id="test_user",
        wiki_dir=str(user_wiki_dir)
    )

    assert res2["status"] == "success"
    log_content = log_md.read_text(encoding="utf-8")
    assert log_content.count("Ingestion Run:") == 2
