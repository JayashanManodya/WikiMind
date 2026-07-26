import io
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from BackEnd.main import app
from BackEnd.services.qa_service import qa_service, REFUSAL_MESSAGE

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_qa_knowledge_base():
    """Populate test knowledge base with Tesla, Elon Musk, and Electric Vehicles"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Tesla is an electric vehicle manufacturer founded by Elon Musk in 2003. "
        "Tesla produces Electric Vehicles with advanced lithium-ion battery technology."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    file = ("tesla_qa_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    file_id = upload_res.json()["file_id"]

    client.post(f"/documents/{file_id}/generate-wiki")
    client.post("/search/index-wiki")

def test_qa_direct_question():
    """Verify direct question 'Who founded Tesla?' returns Elon Musk with citations"""
    res = qa_service.answer_question("Who founded Tesla?")
    assert res.grounded is True
    assert "elon musk" in res.answer.lower()
    assert len(res.citations) >= 1
    assert any(".md" in c for c in res.citations)

def test_qa_comparison_question():
    """Verify comparison question 'Compare Tesla and Electric Vehicles'"""
    res = qa_service.answer_question("Compare Tesla and Electric Vehicles")
    assert res.grounded is True
    assert len(res.answer) > 0
    assert len(res.citations) >= 1

def test_qa_cross_document_reasoning():
    """Verify multi-hop cross-document reasoning spanning Tesla and Elon Musk"""
    res = qa_service.answer_question("What company did Elon Musk founder and what do they produce?")
    assert res.grounded is True
    assert "tesla" in res.answer.lower() or "electric vehicles" in res.answer.lower()

def test_qa_unknown_question_refusal():
    """Verify unknown question 'Who is the president of Mars?' explicitly refuses without hallucination"""
    res = qa_service.answer_question("Who is the president of Mars and when was Microsoft founded?")
    assert res.grounded is False
    assert res.status == "refused"
    assert REFUSAL_MESSAGE in res.answer
    assert len(res.citations) == 0

def test_qa_api_endpoint():
    """Verify POST /qa/ask endpoint returns structured QAResponse"""
    payload = {
        "question": "Who founded Tesla?",
        "top_k": 3,
        "max_chars": 4000
    }
    res = client.post("/qa/ask", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["question"] == "Who founded Tesla?"
    assert "answer" in data
    assert "citations" in data
    assert "grounded" in data

def test_empty_question_qa_returns_400():
    """Verify POST /qa/ask with empty question string returns HTTP 400"""
    payload = {
        "question": "   ",
        "top_k": 3,
        "max_chars": 4000
    }
    res = client.post("/qa/ask", json=payload)
    assert res.status_code == 400
