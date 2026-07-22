import os
import io
import fitz  # PyMuPDF
import docx
import pytest
from fastapi.testclient import TestClient
from BackEnd.main import app

client = TestClient(app)

def create_mock_pdf_bytes(pages_text: list[str]) -> bytes:
    """Helper to generate valid PDF binary bytes using PyMuPDF"""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_parse_simple_pdf():
    """Verify PyMuPDF extracts text cleanly from a 1-page PDF document"""
    sample_text = "WikiMind Simple PDF Test Page Content"
    pdf_bytes = create_mock_pdf_bytes([sample_text])
    
    # 1. Upload
    file = ("simple.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    assert upload_res.status_code == 200
    file_id = upload_res.json()["file_id"]
    
    # 2. Parse
    parse_res = client.post(f"/documents/{file_id}/parse")
    assert parse_res.status_code == 200
    
    data = parse_res.json()
    assert data["file_id"] == file_id
    assert data["total_pages"] == 1
    assert len(data["pages"]) == 1
    assert sample_text in data["pages"][0]["text"]
    assert data["status"] == "parsed"

def test_parse_multipage_pdf_ordering():
    """Verify multi-page PDF extracts pages in exact sequential order (Page 1, Page 2, Page 3) without missing pages"""
    pages_text = [
        "First Section: Introduction to Knowledge Systems",
        "Second Section: Data Processing and Storage Architecture",
        "Third Section: Artificial Intelligence Knowledge Retrieval"
    ]
    pdf_bytes = create_mock_pdf_bytes(pages_text)
    
    file = ("multipage.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    file_id = upload_res.json()["file_id"]
    
    parse_res = client.post(f"/documents/{file_id}/parse")
    assert parse_res.status_code == 200
    
    data = parse_res.json()
    assert data["total_pages"] == 3
    assert len(data["pages"]) == 3
    
    for idx, expected_text in enumerate(pages_text):
        page = data["pages"][idx]
        assert page["page_number"] == idx + 1
        assert expected_text in page["text"]

def test_parse_pdf_with_images_inside():
    """Verify PDF containing drawings/images is parsed without corruption or errors"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Text before image drawing")
    
    # Draw shape / vector graphics representing an image
    rect = fitz.Rect(50, 100, 200, 200)
    page.draw_rect(rect, color=(1, 0, 0), fill=(0, 1, 0))
    page.insert_text((50, 220), "Text after image drawing")
    
    pdf_bytes = doc.tobytes()
    doc.close()
    
    file = ("image_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    file_id = upload_res.json()["file_id"]
    
    parse_res = client.post(f"/documents/{file_id}/parse")
    assert parse_res.status_code == 200
    
    data = parse_res.json()
    assert "Text before image drawing" in data["full_text"]
    assert "Text after image drawing" in data["full_text"]

def test_parse_pdf_with_tables():
    """Verify PDF with table text is extracted into readable plain text"""
    table_text = "Header A\tHeader B\tHeader C\nRow 1\tVal 1\tVal 2\nRow 2\tVal 3\tVal 4"
    pdf_bytes = create_mock_pdf_bytes([table_text])
    
    file = ("table_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    file_id = upload_res.json()["file_id"]
    
    parse_res = client.post(f"/documents/{file_id}/parse")
    assert parse_res.status_code == 200
    
    data = parse_res.json()
    assert "Header A" in data["full_text"]
    assert "Row 1" in data["full_text"]

def test_parse_large_document():
    """Verify 20-page large PDF parses efficiently with correct total page count"""
    large_pages = [f"Page {i} content data section" for i in range(1, 21)]
    pdf_bytes = create_mock_pdf_bytes(large_pages)
    
    file = ("large_book.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    file_id = upload_res.json()["file_id"]
    
    parse_res = client.post(f"/documents/{file_id}/parse")
    assert parse_res.status_code == 200
    
    data = parse_res.json()
    assert data["total_pages"] == 20
    assert len(data["pages"]) == 20
    assert "Page 20 content data section" in data["pages"][19]["text"]

def test_parse_docx_document():
    """Verify DOCX document parsing using python-docx extracts paragraphs and tables"""
    doc = docx.Document()
    doc.add_heading("WikiMind DOCX Specification", level=1)
    doc.add_paragraph("Paragraph 1: Overview of system architecture.")
    
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Column 1"
    table.cell(0, 1).text = "Column 2"
    table.cell(1, 0).text = "Data A"
    table.cell(1, 1).text = "Data B"
    
    buffer = io.BytesIO()
    doc.save(buffer)
    docx_bytes = buffer.getvalue()
    
    file = ("specification.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    upload_res = client.post("/upload", files={"file": file})
    file_id = upload_res.json()["file_id"]
    
    parse_res = client.post(f"/documents/{file_id}/parse")
    assert parse_res.status_code == 200
    
    data = parse_res.json()
    assert "WikiMind DOCX Specification" in data["full_text"]
    assert "Paragraph 1" in data["full_text"]
    assert "Column 1 | Column 2" in data["full_text"]

def test_parse_txt_md_document():
    """Verify TXT and Markdown files parse cleanly"""
    md_content = b"# WikiMind Knowledge Base\n\nThis is plain text markdown document content."
    file = ("knowledge.md", io.BytesIO(md_content), "text/markdown")
    
    upload_res = client.post("/upload", files={"file": file})
    file_id = upload_res.json()["file_id"]
    
    parse_res = client.post(f"/documents/{file_id}/parse")
    assert parse_res.status_code == 200
    
    data = parse_res.json()
    assert "WikiMind Knowledge Base" in data["full_text"]

def test_get_parsed_document_endpoint():
    """Verify GET /documents/{file_id}/parsed retrieves stored JSON output"""
    pdf_bytes = create_mock_pdf_bytes(["Test cached parsed output endpoint"])
    file = ("cached.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    
    upload_res = client.post("/upload", files={"file": file})
    file_id = upload_res.json()["file_id"]
    
    # First parse
    client.post(f"/documents/{file_id}/parse")
    
    # Second fetch
    get_res = client.get(f"/documents/{file_id}/parsed")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["file_id"] == file_id
    assert "Test cached parsed output endpoint" in data["full_text"]

def test_get_parsed_nonexistent_returns_404():
    """Verify GET /documents/{fake_id}/parsed returns HTTP 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = client.get(f"/documents/{fake_id}/parsed")
    assert res.status_code == 404
