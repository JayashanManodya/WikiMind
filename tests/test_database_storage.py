import io
import fitz  # PyMuPDF
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from BackEnd.main import app
from BackEnd.services.db_service import db_service
from BackEnd.models import (
    DocumentModel,
    EntityModel,
    DefinitionModel,
    FactModel,
    RelationshipModel,
    WikiPageModel
)

client = TestClient(app)

def test_database_tables_creation():
    """Verify SQLite database file wikimind.db exists and database tables are created"""
    db_file = Path("./storage/wikimind.db")
    assert db_file.exists() or Path("./BackEnd/storage/wikimind.db").exists()
    
    stats = db_service.get_database_stats()
    assert "total_documents" in stats
    assert "total_entities" in stats
    assert "total_wiki_pages" in stats

def test_full_pipeline_database_persistence():
    """Verify document upload -> knowledge extraction -> wiki generation persists records across all DB tables"""
    # 1. Generate sample PDF content
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Tesla was founded by Elon Musk in 2003. Tesla produces Electric Vehicles.")
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Upload file
    file = ("tesla_db_pipeline.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_res = client.post("/upload", files={"file": file})
    assert upload_res.status_code == 200
    file_id = upload_res.json()["file_id"]

    # Check DocumentModel inserted in DB
    db_doc = db_service.get_document(file_id)
    assert db_doc is not None
    assert db_doc.original_filename == "tesla_db_pipeline.pdf"

    # 3. Extract Knowledge
    extract_res = client.post(f"/documents/{file_id}/extract-knowledge")
    assert extract_res.status_code == 200

    # Check EntityModel and RelationshipModel inserted in DB
    session = db_service.get_session()
    try:
        entities = session.query(EntityModel).filter(EntityModel.file_id == file_id).all()
        assert len(entities) >= 2
        entity_names = [e.name for e in entities]
        assert "Tesla" in entity_names

        relationships = session.query(RelationshipModel).filter(RelationshipModel.file_id == file_id).all()
        assert len(relationships) >= 1
    finally:
        session.close()

    # 4. Generate Wiki
    wiki_res = client.post(f"/documents/{file_id}/generate-wiki")
    assert wiki_res.status_code == 200

    # Check WikiPageModel inserted in DB
    wiki_page = db_service.get_wiki_page_by_name("Tesla")
    assert wiki_page is not None
    assert wiki_page.filename == "Tesla.md"

def test_database_stats_endpoint():
    """Verify GET /database/stats endpoint returns correct record metrics"""
    res = client.get("/database/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_documents"] >= 1
    assert data["total_entities"] >= 1

def test_database_entities_and_relationships_endpoints():
    """Verify GET /database/entities and GET /database/relationships query endpoints"""
    entities_res = client.get("/database/entities")
    assert entities_res.status_code == 200
    entities_data = entities_res.json()
    assert len(entities_data) >= 1

    rels_res = client.get("/database/relationships")
    assert rels_res.status_code == 200
    rels_data = rels_res.json()
    assert len(rels_data) >= 1
