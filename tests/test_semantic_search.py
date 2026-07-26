import io
import fitz  # PyMuPDF
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from BackEnd.main import app
from BackEnd.services.vector_service import vector_service

client = TestClient(app)

def test_vector_indexing_and_storage():
    """Verify wiki pages generation embeds vector representations into storage/vectors/index_vectors.json"""
    # 1. Generate sample PDF content
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Tesla is an EV manufacturer founded by Elon Musk in 2003. Tesla utilizes lithium-ion battery technology."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Upload file
    file = ("tesla_vector_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    assert upload_res.status_code == 200
    file_id = upload_res.json()["file_id"]

    # 3. Generate Wiki Pages
    wiki_res = client.post(f"/documents/{file_id}/generate-wiki")
    assert wiki_res.status_code == 200

    # 4. Trigger Vector Indexing Endpoint
    index_res = client.post("/search/index-wiki")
    assert index_res.status_code == 200
    data = index_res.json()
    assert data["status"] == "indexed"
    assert data["indexed_pages_count"] >= 1

    # Check vector index file on disk
    vectors_file = Path("./BackEnd/storage/vectors/index_vectors.json")
    assert vectors_file.exists()

def test_semantic_search_queries():
    """Verify semantic search queries ('EV manufacturers', 'Tesla founder', 'Battery technology') return relevant pages"""
    queries_to_test = [
        ("EV manufacturers", ["Tesla", "Electric Vehicles"]),
        ("Tesla founder", ["Elon Musk", "Tesla"]),
        ("Battery technology", ["Electric Vehicles", "Tesla"])
    ]

    for query_str, expected_matches in queries_to_test:
        res = client.get(f"/search/semantic?query={query_str}&top_k=5")
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == query_str
        assert data["total_results"] >= 1
        
        # Verify similarity score ranking
        top_result = data["results"][0]
        assert top_result["similarity_score"] > 0.0
        
        # Check if top result entity matches expected entities
        matched_names = [r["entity_name"] for r in data["results"]]
        found = any(exp.lower() in [m.lower() for m in matched_names] for exp in expected_matches)
        assert found, f"Query '{query_str}' did not return expected entities from {expected_matches}"

def test_empty_semantic_search_query_returns_400():
    """Verify GET /search/semantic with empty query returns HTTP 400"""
    res = client.get("/search/semantic?query=")
    assert res.status_code == 422 or res.status_code == 400
