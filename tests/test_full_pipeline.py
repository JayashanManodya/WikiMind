import io
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from BackEnd.main import app

client = TestClient(app)

def test_one_click_upload_auto_process():
    """Verify POST /upload?auto_process=true uploads, parses, cleans, extracts DB, generates wiki, and indexes vectors in 1 call"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Tesla is an electric vehicle manufacturer founded by Elon Musk in 2003."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    file = ("auto_pipeline_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    res = client.post("/upload?auto_process=true", files={"file": file})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "fully_processed"
    assert "fully ingested" in data["message"]

def test_manual_full_pipeline_endpoint():
    """Verify POST /documents/{file_id}/process-full-pipeline manually triggers full ingestion pipeline"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Tesla produces Electric Vehicles with lithium-ion battery technology."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    file = ("manual_pipeline_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload?auto_process=false", files={"file": file})
    assert upload_res.status_code == 200
    file_id = upload_res.json()["file_id"]

    # Trigger manual pipeline endpoint
    pipeline_res = client.post(f"/documents/{file_id}/process-full-pipeline")
    assert pipeline_res.status_code == 200
    data = pipeline_res.json()
    assert data["status"] == "fully_processed"
    assert data["vector_indexed"] is True
    assert data["wiki_pages_generated"] >= 1

def test_immediate_qa_after_auto_process_upload():
    """Verify immediate QA works instantly after auto_process upload without extra calls"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Tesla was founded by Elon Musk in 2003."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    file = ("instant_qa_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload?auto_process=true", files={"file": file})
    assert upload_res.status_code == 200

    # Ask Question Immediately
    qa_res = client.post("/qa/ask", json={"question": "Who founded Tesla?", "top_k": 3})
    assert qa_res.status_code == 200
    qa_data = qa_res.json()
    assert qa_data["grounded"] is True
    assert "elon musk" in qa_data["answer"].lower()
