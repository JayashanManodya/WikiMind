import os
import io
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from BackEnd.main import app

client = TestClient(app)

def test_upload_single_pdf():
    """Verify single PDF document upload, file storage in documents/, and metadata creation"""
    pdf_content = b"%PDF-1.4 Mock single PDF file content for Phase 4 WikiMind test"
    file = ("single_test.pdf", io.BytesIO(pdf_content), "application/pdf")
    
    response = client.post("/upload", files={"file": file})
    assert response.status_code == 200
    
    data = response.json()
    assert data["filename"] == "single_test.pdf"
    assert data["size_bytes"] == len(pdf_content)
    assert "file_id" in data
    
    saved_path = data["saved_path"]
    assert "documents" in saved_path
    assert os.path.exists(saved_path)
    
    # Metadata assertion
    assert "metadata" in data
    meta = data["metadata"]
    assert meta["file_id"] == data["file_id"]
    assert meta["sha256_hash"] is not None
    assert meta["status"] == "stored"

def test_upload_10_pdfs_batch():
    """Verify uploading a batch of 10 PDFs generates 10 unique UUID-named files without collision"""
    saved_paths = []
    file_ids = set()
    
    for i in range(10):
        pdf_content = f"%PDF-1.4 Content for PDF document #{i}".encode("utf-8")
        file = (f"document_batch_{i}.pdf", io.BytesIO(pdf_content), "application/pdf")
        
        response = client.post("/upload", files={"file": file})
        assert response.status_code == 200
        
        data = response.json()
        saved_paths.append(data["saved_path"])
        file_ids.add(data["file_id"])
    
    # Assert all 10 file IDs are distinct UUIDs
    assert len(file_ids) == 10
    
    # Assert all 10 files exist on disk
    for path in saved_paths:
        assert os.path.exists(path)

def test_upload_large_pdf():
    """Verify 10MB large PDF streams, saves, and calculates correct byte count and SHA256 hash"""
    large_size = 10 * 1024 * 1024  # 10MB
    large_content = b"P" * large_size
    file = ("large_research_paper.pdf", io.BytesIO(large_content), "application/pdf")
    
    response = client.post("/upload", files={"file": file})
    assert response.status_code == 200
    
    data = response.json()
    assert data["size_bytes"] == large_size
    assert os.path.exists(data["saved_path"])

def test_upload_empty_pdf_rejected():
    """Verify empty 0-byte PDF upload is rejected with HTTP 400"""
    empty_content = b""
    file = ("empty_document.pdf", io.BytesIO(empty_content), "application/pdf")
    
    response = client.post("/upload", files={"file": file})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "empty" in data["detail"].lower()

def test_upload_wrong_extension_rejected():
    """Verify unsupported file format (.exe) is rejected with HTTP 400"""
    exe_content = b"MZ executable binary payload"
    file = ("malicious_file.exe", io.BytesIO(exe_content), "application/x-msdownload")
    
    response = client.post("/upload", files={"file": file})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Unsupported file format" in data["detail"]

def test_upload_duplicate_filename_no_overwrite():
    """Verify uploading two files with identical original filenames creates 2 distinct stored files without overwriting"""
    content_v1 = b"%PDF-1.4 Version 1 content of report"
    content_v2 = b"%PDF-1.4 Version 2 content of report (different size)"
    
    file_v1 = ("annual_report.pdf", io.BytesIO(content_v1), "application/pdf")
    file_v2 = ("annual_report.pdf", io.BytesIO(content_v2), "application/pdf")
    
    res1 = client.post("/upload", files={"file": file_v1})
    res2 = client.post("/upload", files={"file": file_v2})
    
    assert res1.status_code == 200
    assert res2.status_code == 200
    
    data1 = res1.json()
    data2 = res2.json()
    
    # Assert different file IDs and distinct saved paths
    assert data1["file_id"] != data2["file_id"]
    assert data1["saved_path"] != data2["saved_path"]
    
    # Assert both files exist simultaneously on disk with their original uncorrupted contents
    assert os.path.exists(data1["saved_path"])
    assert os.path.exists(data2["saved_path"])
    
    with open(data1["saved_path"], "rb") as f1:
        assert f1.read() == content_v1
    with open(data2["saved_path"], "rb") as f2:
        assert f2.read() == content_v2

def test_documents_metadata_endpoints():
    """Verify GET /documents lists all documents and GET /documents/{file_id} retrieves specific metadata"""
    # 1. Upload a document
    pdf_content = b"%PDF-1.4 Metadata inspection test PDF content"
    file = ("metadata_test.pdf", io.BytesIO(pdf_content), "application/pdf")
    
    upload_res = client.post("/upload", files={"file": file})
    assert upload_res.status_code == 200
    file_id = upload_res.json()["file_id"]
    
    # 2. Query GET /documents
    list_res = client.get("/documents")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total_documents"] >= 1
    assert any(doc["file_id"] == file_id for doc in list_data["documents"])
    
    # 3. Query GET /documents/{file_id}
    detail_res = client.get(f"/documents/{file_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["file_id"] == file_id
    assert detail_data["original_filename"] == "metadata_test.pdf"
    assert detail_data["size_bytes"] == len(pdf_content)

def test_get_nonexistent_document_metadata_returns_404():
    """Verify GET /documents/{nonexistent_id} returns HTTP 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = client.get(f"/documents/{fake_id}")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
