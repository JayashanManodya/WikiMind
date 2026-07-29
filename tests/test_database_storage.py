"""Unit tests for Relational Database storage of Wiki pages and Knowledge Graph edges."""

import pytest
from backend.app.core.db import (
    init_db,
    save_wiki_page_db,
    get_wiki_page_db,
    get_user_wiki_pages_db,
    save_graph_edges_db,
    get_user_graph_edges_db
)
from backend.app.core.retrieval.vector_store import index_wiki_documents, retrieve


def test_database_table_initialization():
    """Test initializing database tables."""
    init_db()


def test_wiki_page_save_and_retrieve_db():
    """Test saving and retrieving wiki page content_md in database."""
    user_id = "test_db_user_1"
    entity = "Robotic Control Loop"
    content = "# Robotic Control Loop\n\nOperates at 100Hz with PID feedback controller."

    saved = save_wiki_page_db(
        user_id=user_id,
        entity_name=entity,
        entity_type="SYSTEM",
        filename="Robotic_Control_Loop.md",
        content_md=content,
        summary="PID feedback loop",
        related_entities=["PID Controller", "Sensor Feedback"]
    )

    assert saved["id"] == f"{user_id}:{entity}"

    retrieved = get_wiki_page_db(user_id, entity)
    assert retrieved is not None
    assert retrieved["content_md"] == content
    assert retrieved["entity_type"] == "SYSTEM"
    assert "PID Controller" in retrieved["related_entities"]


def test_graph_edges_save_and_retrieve_db():
    """Test saving and retrieving relationship edges in wiki_graph_edges database table."""
    user_id = "test_db_user_2"
    relationships = [
        {"source": "Robotic Arm", "relation": "USES_MOTOR", "target": "Stepper Motor 24V"},
        {"source": "Robotic Arm", "relation": "CONTROLLED_BY", "target": "ESP32 Controller"}
    ]

    save_graph_edges_db(user_id=user_id, relationships=relationships)
    edges = get_user_graph_edges_db(user_id)
    assert len(edges) >= 2
    sources = [e["source"] for e in edges]
    assert "Robotic Arm" in sources


def test_database_vector_retrieval_end_to_end():
    """Test end-to-end vector search and SQL database page retrieval."""
    user_id = "test_db_user_3"
    wiki_pages = [
        {
            "entity_name": "Thermal Sensor Module",
            "filename": "Thermal_Sensor_Module.md",
            "content": "# Thermal Sensor Module\n\nUses [[DHT22 Sensor]] to measure 25.0C operating temperature.",
            "entity_type": "HARDWARE"
        },
        {
            "entity_name": "DHT22 Sensor",
            "filename": "DHT22_Sensor.md",
            "content": "# DHT22 Sensor\n\nDigital temperature and humidity sensor module with 3.3V power.",
            "entity_type": "COMPONENT"
        }
    ]

    for p in wiki_pages:
        save_wiki_page_db(
            user_id=user_id,
            entity_name=p["entity_name"],
            entity_type=p["entity_type"],
            filename=p["filename"],
            content_md=p["content"],
            related_entities=["DHT22 Sensor"] if p["entity_name"] == "Thermal Sensor Module" else []
        )

    # Index into vector store
    index_wiki_documents(wiki_pages, user_id=user_id)

    # Retrieve via vector store + 1-hop graph expansion
    docs = retrieve("What temperature sensor is used?", user_id=user_id)
    assert len(docs) >= 1
    content_text = " ".join([d.page_content for d in docs])
    assert "DHT22" in content_text


def test_zero_md_file_disk_creation(tmp_path):
    """Test that update_or_create_wiki_pages creates zero .md files on disk."""
    from backend.app.core.ingestion.wiki_engine import update_or_create_wiki_pages

    user_dir = tmp_path / "wiki" / "users" / "test_zero_disk_user"
    user_dir.mkdir(parents=True)

    knowledge_json = {
        "entities": [
            {"name": "Zero Disk Engine", "type": "SYSTEM", "description": "Operates purely in memory and DB."}
        ],
        "relationships": []
    }

    res = update_or_create_wiki_pages(knowledge_json, "doc.pdf", str(user_dir))

    # Verify database record exists
    rec = get_wiki_page_db("test_zero_disk_user", "Zero Disk Engine")
    assert rec is not None
    assert "Zero Disk Engine" in rec["content_md"]

    # Verify zero .md files written to disk
    md_files = list(user_dir.glob("*.md"))
    assert len(md_files) == 0


def test_cumulative_user_wiki_index_and_graph():
    """Test that Wiki index and graph accumulate all entity pages across multiple uploads."""
    user_id = "test_cumulative_user"

    # Upload 1: Project Document
    save_wiki_page_db(user_id, "Project Alpha", "PRODUCT", "alpha.pdf", "# Project Alpha")
    save_graph_edges_db(user_id, [{"source": "Project Alpha", "relation": "USES", "target": "Python"}])

    # Upload 2: Person Resume Document
    save_wiki_page_db(user_id, "Alice Developer", "PERSON", "resume.pdf", "# Alice Developer")
    save_wiki_page_db(user_id, "Python", "TECHNOLOGY", "resume.pdf", "# Python")
    save_graph_edges_db(user_id, [{"source": "Alice Developer", "relation": "SKILLED_IN", "target": "Python"}])

    db_pages = get_user_wiki_pages_db(user_id)
    db_edges = get_user_graph_edges_db(user_id)

    assert len(db_pages) == 3
    entity_names = [p["entity_name"] for p in db_pages]
    assert "Project Alpha" in entity_names
    assert "Alice Developer" in entity_names
    assert "Python" in entity_names
    assert len(db_edges) >= 2


