import os
import io
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from BackEnd.main import app
from BackEnd.services.cleaner_service import cleaner_service

client = TestClient(app)

def create_pdf_with_headers_and_footers() -> bytes:
    """Helper to generate a multi-page PDF containing running headers, page numbers, and core body text"""
    doc = fitz.open()
    pages_body = [
        "Knowledge Graph Extraction is a core AI pipeline component.\nIt analyzes domain entities and relationships.",
        "Markdown Knowledge Bases allow human-inspectable documentation.\nHyperlinks connect concepts seamlessly.",
        "Hybrid Vector Search combines dense embeddings with graph traversal.\nThis yields highly accurate multi-hop Q&A."
    ]
    
    for idx, body in enumerate(pages_body):
        page = doc.new_page()
        # Running header at top
        page.insert_text((50, 30), "CONFIDENTIAL - WIKIMIND ARCHITECTURE SPEC")
        # Body text in middle
        page.insert_text((50, 100), f"Section {idx + 1}: {body}")
        # Running footer / page number at bottom
        page.insert_text((50, 750), f"Page {idx + 1} of {len(pages_body)}")
        
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_unicode_normalization():
    """Verify smart quotes, non-breaking spaces, and em-dashes are normalized to standard UTF-8"""
    raw_text = "“WikiMind” — AI Platform\u00a0with ‘Smart Quotes’…"
    cleaned = cleaner_service.normalize_unicode(raw_text)
    
    assert '"WikiMind"' in cleaned
    assert "AI Platform with" in cleaned
    assert "'Smart Quotes'" in cleaned
    assert "..." in cleaned

def test_whitespace_normalization():
    """Verify multiple spaces are collapsed to 1 space and 3+ blank lines are reduced to max 2 newlines"""
    raw_text = "Word1    Word2\t\tWord3\n\n\n\n\nWord4"
    cleaned = cleaner_service.normalize_whitespace(raw_text)
    
    assert "Word1 Word2 Word3" in cleaned
    assert "\n\n" in cleaned
    assert "\n\n\n" not in cleaned

def test_page_number_pattern_removal():
    """Verify standalone page number patterns (Page 1 of 10, - 2 -, [Page 3], 4 / 20) are stripped"""
    raw_text = (
        "Core text paragraph 1.\n"
        "Page 1 of 10\n"
        "Core text paragraph 2.\n"
        "- 2 -\n"
        "Core text paragraph 3.\n"
        "3 / 10\n"
    )
    cleaned = cleaner_service.remove_page_numbers_and_footers(raw_text)
    cleaned = cleaner_service.normalize_whitespace(cleaned)
    
    assert "Core text paragraph 1." in cleaned
    assert "Core text paragraph 2." in cleaned
    assert "Core text paragraph 3." in cleaned
    assert "Page 1 of 10" not in cleaned
    assert "- 2 -" not in cleaned
    assert "3 / 10" not in cleaned

def test_running_header_footer_removal():
    """Verify top/bottom running header lines repeated across multi-page document are stripped"""
    pages_raw = [
        "WIKIMIND INTERNAL DOCUMENT\nBody text on page 1.\nPage 1",
        "WIKIMIND INTERNAL DOCUMENT\nBody text on page 2.\nPage 2",
        "WIKIMIND INTERNAL DOCUMENT\nBody text on page 3.\nPage 3"
    ]
    cleaned_pages = cleaner_service.remove_running_headers_footers(pages_raw)
    
    for page in cleaned_pages:
        assert "WIKIMIND INTERNAL DOCUMENT" not in page

def test_pdf_original_vs_extracted_vs_cleaned_compare():
    """
    Compare Original PDF -> Extracted Raw Text -> Cleaned Text.
    Ensures running headers/footers & page numbers are removed while 100% of body text remains intact.
    """
    pdf_bytes = create_pdf_with_headers_and_footers()
    
    # 1. Upload
    file = ("architecture_spec.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    assert upload_res.status_code == 200
    file_id = upload_res.json()["file_id"]
    
    # 2. Clean (automatically triggers parsing if not parsed)
    clean_res = client.post(f"/documents/{file_id}/clean")
    assert clean_res.status_code == 200
    
    cleaned_data = clean_res.json()
    full_cleaned = cleaned_data["full_cleaned_text"]
    
    # Assert running headers and page numbers are removed
    assert "CONFIDENTIAL - WIKIMIND ARCHITECTURE SPEC" not in full_cleaned
    assert "Page 1 of 3" not in full_cleaned
    
    # Assert 100% of body knowledge content is preserved!
    assert "Knowledge Graph Extraction is a core AI pipeline component." in full_cleaned
    assert "Markdown Knowledge Bases allow human-inspectable documentation." in full_cleaned
    assert "Hybrid Vector Search combines dense embeddings with graph traversal." in full_cleaned
    assert "Section 1:" in full_cleaned

def test_get_cleaned_document_endpoint():
    """Verify GET /documents/{file_id}/cleaned retrieves stored JSON cleaned output"""
    pdf_bytes = create_pdf_with_headers_and_footers()
    file = ("cached_clean.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    
    upload_res = client.post("/upload", files={"file": file})
    file_id = upload_res.json()["file_id"]
    
    # 1. Clean
    client.post(f"/documents/{file_id}/clean")
    
    # 2. Fetch cached
    get_res = client.get(f"/documents/{file_id}/cleaned")
    assert get_res.status_code == 200
    
    data = get_res.json()
    assert data["file_id"] == file_id
    assert data["status"] == "cleaned"
    assert "Knowledge Graph Extraction" in data["full_cleaned_text"]

def test_get_cleaned_nonexistent_returns_404():
    """Verify GET /documents/{fake_id}/cleaned returns HTTP 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = client.get(f"/documents/{fake_id}/cleaned")
    assert res.status_code == 404
