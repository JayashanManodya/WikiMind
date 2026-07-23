import io
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from BackEnd.main import app
from BackEnd.services.llm_service import llm_service

client = TestClient(app)

def test_extract_knowledge_sample_input():
    """Verify input 'Tesla was founded by Elon Musk in 2003.' extracts entities, relationship, facts, and summary"""
    sample_text = "Tesla was founded by Elon Musk in 2003."
    extraction = llm_service.extract_knowledge_deterministic(sample_text)
    
    assert "summary" in extraction
    assert len(extraction["entities"]) >= 2
    
    entity_names = [e["name"] for e in extraction["entities"]]
    assert "Tesla" in entity_names
    assert "Elon Musk" in entity_names
    
    assert len(extraction["relationships"]) >= 1
    rel = extraction["relationships"][0]
    assert rel["source_entity"] == "Tesla"
    assert rel["relation"] == "FOUNDED_BY"
    assert rel["target_entity"] == "Elon Musk"
    
    assert len(extraction["facts"]) >= 1
    assert "Tesla was founded by Elon Musk" in extraction["facts"][0]["fact"]

def test_extract_knowledge_complex_document():
    """Verify multi-paragraph technical document extracts definitions, entities, relationships, and facts"""
    doc_text = (
        "WikiMind is an AI platform created by Antigravity.\n"
        "Knowledge Graph is defined as a structured representation of interconnected concepts and entities.\n"
        "FastAPI is a modern web framework used for high performance API development.\n"
        "WikiMind uses FastAPI for backend routing."
    )
    extraction = llm_service.extract_knowledge_deterministic(doc_text)
    
    # Check definitions
    assert len(extraction["definitions"]) >= 1
    def_terms = [d["term"] for d in extraction["definitions"]]
    assert "Knowledge Graph" in def_terms
    
    # Check relationships
    rel_tuples = [(r["source_entity"], r["relation"], r["target_entity"]) for r in extraction["relationships"]]
    assert ("WikiMind", "CREATED_BY", "Antigravity") in rel_tuples or ("WikiMind", "USES", "FastAPI") in rel_tuples

def test_knowledge_extraction_api_endpoints():
    """Verify POST /documents/{file_id}/extract-knowledge and GET /documents/{file_id}/knowledge endpoints"""
    # 1. Generate PDF with sample content
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Tesla was founded by Elon Musk in 2003.")
    pdf_bytes = doc.tobytes()
    doc.close()
    
    # 2. Upload
    file = ("tesla_founding.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    assert upload_res.status_code == 200
    file_id = upload_res.json()["file_id"]
    
    # 3. Trigger Knowledge Extraction
    extract_res = client.post(f"/documents/{file_id}/extract-knowledge")
    assert extract_res.status_code == 200
    
    data = extract_res.json()
    assert data["file_id"] == file_id
    assert data["status"] == "extracted"
    assert len(data["entities"]) >= 2
    assert len(data["relationships"]) >= 1
    
    # 4. Fetch stored knowledge artifact
    get_res = client.get(f"/documents/{file_id}/knowledge")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["file_id"] == file_id
    assert get_data["summary"] is not None

def test_get_knowledge_nonexistent_returns_404():
    """Verify GET /documents/{fake_id}/knowledge returns HTTP 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = client.get(f"/documents/{fake_id}/knowledge")
    assert res.status_code == 404

def test_hallucination_prevention_filter():
    """Verify filter_hallucinations strips entities/relationships not grounded in text"""
    text = "Tesla was founded by Elon Musk."
    fake_raw = {
        "summary": "Tesla overview",
        "entities": [
            {"name": "Tesla", "type": "ORGANIZATION", "description": "EV company"},
            {"name": "Elon Musk", "type": "PERSON", "description": "Founder"},
            {"name": "Hallucinated Company XYZ", "type": "ORGANIZATION", "description": "Fake entity"}
        ],
        "relationships": [
            {"source_entity": "Tesla", "relation": "FOUNDED_BY", "target_entity": "Elon Musk", "description": "Founded"},
            {"source_entity": "Tesla", "relation": "ACQUIRED", "target_entity": "NonExistent Target Inc", "description": "Fake rel"}
        ]
    }
    filtered = llm_service.filter_hallucinations(fake_raw, text)
    entity_names = [e["name"] for e in filtered["entities"]]
    assert "Tesla" in entity_names
    assert "Elon Musk" in entity_names
    assert "Hallucinated Company XYZ" not in entity_names
    
    assert len(filtered["relationships"]) == 1
    assert filtered["relationships"][0]["target_entity"] == "Elon Musk"

def test_multi_domain_knowledge_extraction():
    """Verify knowledge extraction across domain texts (Financial, Technical, Medical)"""
    domains = [
        ("Financial", "Apple reported revenue of 90 billion USD. Apple was created by Steve Jobs."),
        ("Technical", "PostgreSQL is defined as an open source relational database. PostgreSQL uses SQL for querying."),
        ("Medical", "Penicillin was discovered by Alexander Fleming.")
    ]
    for domain_name, sample in domains:
        extracted = llm_service.extract_knowledge(sample)
        assert len(extracted["summary"]) > 0, f"Summary empty for {domain_name}"
        assert len(extracted["entities"]) >= 1, f"No entities found for {domain_name}"

