import sys
import os
import io
import types
from pathlib import Path
import fitz  # PyMuPDF
import docx
import pytest
from fastapi.testclient import TestClient

# Add project root and backend directory to sys.path
root_dir = Path(__file__).parent.parent
backend_dir = root_dir / "backend"

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import FastAPI app from api module
try:
    from backend.app.api import app
except ImportError:
    from app.api import app

# Provide mock user dependency override so authenticated endpoints work seamlessly in unit tests
from backend.app.core.auth import get_current_user
app.dependency_overrides[get_current_user] = lambda: {
    "user_id": "test_user",
    "email": "test@example.com",
    "name": "Test User"
}

# Create BackEnd.main module alias for backwards compatibility
backend_pkg = types.ModuleType("BackEnd")
main_mod = types.ModuleType("BackEnd.main")
main_mod.app = app
backend_pkg.main = main_mod
sys.modules["BackEnd"] = backend_pkg
sys.modules["BackEnd.main"] = main_mod

client = TestClient(app)


def create_mock_pdf_bytes(pages_text: list[str]) -> bytes:
    """Helper to generate valid PDF binary bytes using PyMuPDF"""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        rect = fitz.Rect(50, 50, 550, 750)
        page.insert_textbox(rect, text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_parse_simple_pdf():
    """Verify PyMuPDF/LlamaParse extracts text cleanly from a 1-page PDF document"""
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
    """Verify multi-page PDF extracts pages in exact sequential order without missing pages"""
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
    assert "Val 3" in data["full_text"]


def test_parse_docx_document():
    """Verify DOCX document with headings and tables is parsed cleanly"""
    doc = docx.Document()
    doc.add_heading("WikiMind DOCX Specification", level=1)
    doc.add_paragraph("Paragraph 1: Core document description.")
    
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Column 1"
    table.cell(0, 1).text = "Column 2"
    table.cell(1, 0).text = "Data 1"
    table.cell(1, 1).text = "Data 2"
    
    buffer = io.BytesIO()
    doc.save(buffer)
    docx_bytes = buffer.getvalue()
    
    file = ("spec.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    upload_res = client.post("/upload", files={"file": file})
    file_id = upload_res.json()["file_id"]
    
    parse_res = client.post(f"/documents/{file_id}/parse")
    assert parse_res.status_code == 200
    
    data = parse_res.json()
    assert "WikiMind DOCX Specification" in data["full_text"]
    assert "Paragraph 1" in data["full_text"]
    assert "Column 1" in data["full_text"]


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


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
