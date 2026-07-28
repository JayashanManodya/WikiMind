import io
import fitz  # PyMuPDF
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from BackEnd.main import app
from BackEnd.services.chroma_service import chroma_service

client = TestClient(app)

def test_unified_pdf_upload_and_chroma_indexing():
    """Verify single-file unified pipeline processes uploaded PDF end-to-end and indexes vectors into ChromaDB"""
    # 1. Create sample PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "ChromaDB is an open-source AI vector database designed to store vector embeddings for semantic search and Retrieval-Augmented Generation (RAG)."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Upload PDF to POST /upload with auto_process=True
    file = ("chromadb_unified_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    res = client.post("/upload?auto_process=true", files={"file": file})
    assert res.status_code == 200
    
    data = res.json()
    assert data["status"] == "fully_processed"
    assert "ChromaDB" in data["message"] or "fully ingested" in data["message"]
    file_id = data["file_id"]

    # 3. Verify ChromaDB Collection has indexed vector documents
    collection_count = chroma_service.collection.count()
    assert collection_count >= 1

    # 4. Perform vector search directly on ChromaDB
    chroma_results = chroma_service.search_vectors("What is ChromaDB?", top_k=3)
    assert len(chroma_results) >= 1
    assert chroma_results[0]["similarity_score"] >= 0.0

    # 5. Verify Grounded QA Engine returns answer using ChromaDB retrieval
    qa_res = client.post("/qa/ask", json={
        "question": "What is ChromaDB used for?",
        "top_k": 3,
        "max_chars": 3000
    })
    assert qa_res.status_code == 200
    qa_data = qa_res.json()
    assert qa_data["grounded"] is True
    assert "vector" in qa_data["answer"].lower() or "chromadb" in qa_data["answer"].lower()
