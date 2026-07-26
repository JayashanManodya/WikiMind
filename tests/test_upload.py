import os
import io
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from BackEnd.main import app

client = TestClient(app)

def test_upload_pdf_success():
    """Verify uploading a valid PDF document succeeds and returns UploadResponse metadata"""
    pdf_content = b"%PDF-1.4 Mock PDF file content for WikiMind ingestion test"
    file = ("sample.pdf", io.BytesIO(pdf_content), "application/pdf")
    
    response = client.post("/upload", files={"file": file})
    assert response.status_code == 200
    
    data = response.json()
    assert data["filename"] == "sample.pdf"
    assert data["status"] in ("uploaded", "fully_processed")
    assert data["size_bytes"] == len(pdf_content)
    assert "file_id" in data
    assert os.path.exists(data["saved_path"])
    
    # Cleanup saved test file
    if os.path.exists(data["saved_path"]):
        os.remove(data["saved_path"])

def test_upload_allowed_extensions():
    """Verify TXT, MD, and DOCX files are accepted"""
    test_files = [
        ("notes.txt", b"Plain text notes content", "text/plain"),
        ("wiki.md", b"# Markdown Knowledge Base Header", "text/markdown"),
        ("document.docx", b"Mock DOCX binary content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    ]
    
    for filename, content, mime in test_files:
        file = (filename, io.BytesIO(content), mime)
        response = client.post("/upload", files={"file": file})
        assert response.status_code == 200, f"Failed uploading {filename}: {response.text}"
        data = response.json()
        assert data["filename"] == filename
        
        # Cleanup
        if os.path.exists(data["saved_path"]):
            os.remove(data["saved_path"])

def test_upload_invalid_file_type_rejected():
    """Verify unsupported file extensions (.exe, .png, .py) are rejected with HTTP 400"""
    invalid_files = [
        ("executable.exe", b"MZ binary payload", "application/x-msdownload"),
        ("image.png", b"\x89PNG\r\n\x1a\nfake png data", "image/png"),
        ("script.py", b"print('hello world')", "text/x-python")
    ]
    
    for filename, content, mime in invalid_files:
        file = (filename, io.BytesIO(content), mime)
        response = client.post("/upload", files={"file": file})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Unsupported file format" in data["detail"]

def test_upload_large_file():
    """Verify large file content (e.g. 5MB dummy buffer) streams and saves cleanly"""
    large_size = 5 * 1024 * 1024  # 5MB
    large_content = b"A" * large_size
    file = ("large_report.pdf", io.BytesIO(large_content), "application/pdf")
    
    response = client.post("/upload", files={"file": file})
    assert response.status_code == 200
    data = response.json()
    assert data["size_bytes"] == large_size
    assert os.path.exists(data["saved_path"])
    
    # Cleanup
    if os.path.exists(data["saved_path"]):
        os.remove(data["saved_path"])
