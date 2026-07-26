import io
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from BackEnd.main import app
from BackEnd.services.graph_service import graph_service

client = TestClient(app)

def test_langgraph_stategraph_initialization():
    """Verify LangGraphEngine compiles ingestion_graph and qa_graph"""
    assert graph_service.ingestion_graph is not None
    assert graph_service.qa_graph is not None

def test_langgraph_ingestion_execution():
    """Verify LangGraph Document Ingestion StateGraph runs across all nodes (parse -> clean -> extract -> wiki -> embed)"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Tesla is an electric vehicle manufacturer founded by Elon Musk in 2003."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    file = ("langgraph_ingest_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload?auto_process=false", files={"file": file})
    assert upload_res.status_code == 200
    file_id = upload_res.json()["file_id"]

    # Execute LangGraph Ingestion StateGraph
    pipeline_res = graph_service.run_ingestion_graph(file_id)
    assert pipeline_res.status == "fully_processed"
    assert pipeline_res.vector_indexed is True
    assert "LangGraph Ingestion Workflow executed successfully" in pipeline_res.message

def test_langgraph_qa_execution():
    """Verify LangGraph QA StateGraph runs across retrieve and LLM QA nodes"""
    res = graph_service.run_qa_graph("Who founded Tesla?", top_k=2, max_chars=3000)
    assert res.grounded is True
    assert "elon musk" in res.answer.lower()
    assert len(res.citations) >= 1

def test_langgraph_error_recovery_routing():
    """Verify failure recovery: invalid file_id routes through error_recovery_node without server crash"""
    pipeline_res = graph_service.run_ingestion_graph("invalid-uuid-99999")
    assert pipeline_res.status == "recovered_with_error"
    assert pipeline_res.vector_indexed is False
