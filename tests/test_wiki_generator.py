import io
import fitz  # PyMuPDF
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from BackEnd.main import app

client = TestClient(app)

def test_generate_wiki_pages_and_index():
    """Verify POST /documents/{file_id}/generate-wiki creates markdown wiki pages and updates index"""
    # 1. Generate PDF with knowledge content
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Tesla was founded by Elon Musk in 2003. Tesla produces Electric Vehicles.")
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Upload file
    file = ("tesla_founding_wiki.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    assert upload_res.status_code == 200
    file_id = upload_res.json()["file_id"]

    # 3. Trigger Wiki Generation
    wiki_res = client.post(f"/documents/{file_id}/generate-wiki")
    assert wiki_res.status_code == 200
    
    data = wiki_res.json()
    assert data["file_id"] == file_id
    assert data["status"] == "wiki_generated"
    assert data["total_pages_generated"] >= 2

    # Check generated files in ./BackEnd/storage/wiki
    wiki_dir = Path("./BackEnd/storage/wiki")
    assert (wiki_dir / "Tesla.md").exists() or (wiki_dir / "Elon_Musk.md").exists()
    assert (wiki_dir / "Index.md").exists()
    assert (wiki_dir / "index.json").exists()

    # Check Markdown Content of Tesla.md
    tesla_content = (wiki_dir / "Tesla.md").read_text(encoding="utf-8")
    assert "# Tesla" in tesla_content
    assert "Elon Musk" in tesla_content
    assert "[[" in tesla_content or "](" in tesla_content  # Internal wiki link syntax

def test_get_wiki_index_endpoint():
    """Verify GET /wiki/index returns list of generated wiki topic pages"""
    res = client.get("/wiki/index")
    assert res.status_code == 200
    data = res.json()
    assert "total_pages" in data
    assert "pages" in data
    assert data["total_pages"] >= 1

def test_get_wiki_page_endpoint():
    """Verify GET /wiki/page/{entity_name} retrieves wiki page details"""
    res = client.get("/wiki/page/Tesla")
    if res.status_code == 404:
        # Fallback if Tesla wasn't generated in previous test, check Index
        index_res = client.get("/wiki/index")
        pages = index_res.json()["pages"]
        if pages:
            first_entity = pages[0]["entity_name"]
            res = client.get(f"/wiki/page/{first_entity}")
            
    assert res.status_code == 200
    data = res.json()
    assert "entity_name" in data
    assert "content" in data
    assert len(data["content"]) > 0

def test_get_wiki_page_nonexistent_returns_404():
    """Verify GET /wiki/page/{fake_entity} returns HTTP 404"""
    res = client.get("/wiki/page/NonExistentFakeEntity12345")
    assert res.status_code == 404
