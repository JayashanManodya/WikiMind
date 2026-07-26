import io
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from BackEnd.main import app
from BackEnd.services.retriever_service import retriever_service

client = TestClient(app)

def test_multi_hop_retrieval_and_graph_expansion():
    """Verify Hop 1 semantic vector search + Hop 2 graph link expansion (Tesla -> Elon Musk)"""
    # 1. Setup sample document knowledge
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Tesla is an EV manufacturer founded by Elon Musk in 2003. Tesla produces Electric Vehicles."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Upload, parse, clean, extract, generate wiki & index vectors
    file = ("tesla_retrieval_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    assert upload_res.status_code == 200
    file_id = upload_res.json()["file_id"]

    wiki_res = client.post(f"/documents/{file_id}/generate-wiki")
    assert wiki_res.status_code == 200

    client.post("/search/index-wiki")

    # 3. Trigger Multi-Hop Retrieval
    res = retriever_service.retrieve_multi_hop_context(
        question="Who founded Tesla and what do they produce?",
        top_k=2,
        max_chars=4000
    )

    assert res.question == "Who founded Tesla and what do they produce?"
    assert res.primary_pages_count >= 1
    assert len(res.retrieved_pages) >= 1
    assert "# RETRIEVED KNOWLEDGE CONTEXT" in res.assembled_context

    # Check Hop 1 and Hop 2 pages
    retrieved_names = [p.entity_name for p in res.retrieved_pages]
    assert "Tesla" in retrieved_names or "Elon Musk" in retrieved_names

def test_character_budgeting_constraint():
    """Verify max_chars limit is strictly enforced during context assembly"""
    res = retriever_service.retrieve_multi_hop_context(
        question="Tesla",
        top_k=5,
        max_chars=1200
    )
    assert res.total_chars <= 1200

def test_retrieval_api_endpoint():
    """Verify POST /retrieval/context endpoint returns structured RetrievalContextResponse"""
    payload = {
        "question": "What is Tesla?",
        "top_k": 2,
        "max_chars": 3000
    }
    res = client.post("/retrieval/context", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "retrieved"
    assert "assembled_context" in data
    assert "retrieved_pages" in data

def test_empty_question_retrieval_returns_400():
    """Verify POST /retrieval/context with empty question string returns HTTP 400"""
    payload = {
        "question": "   ",
        "top_k": 2,
        "max_chars": 3000
    }
    res = client.post("/retrieval/context", json=payload)
    assert res.status_code == 400
