"""Unit tests for Knowledge Graph Connectivity guarantees (Zero isolated nodes)."""

import pytest
from pathlib import Path
from backend.app.core.ingestion.extractor import _enforce_no_isolated_entities
from backend.app.core.ingestion.index_manager import update_wiki_index_catalog
from backend.app.core.ingestion.wiki_engine import update_or_create_wiki_pages


def test_extractor_enforces_no_isolated_entities():
    """Test that extractor synthesizes relationships for isolated entities."""
    knowledge_json = {
        "title": "Quantum Computing Document",
        "entities": [
            {"name": "Quantum Computing", "type": "CONCEPT", "description": "Main topic"},
            {"name": "Qubit", "type": "TECHNOLOGY", "description": "Quantum bit"},
            {"name": "Superposition", "type": "CONCEPT", "description": "State"},
        ],
        "concepts": [],
        "relationships": []  # Zero relationships initially
    }

    _enforce_no_isolated_entities(knowledge_json, "quantum_doc.txt", {"title": "Quantum Computing Document"})

    rels = knowledge_json["relationships"]
    assert len(rels) >= 2

    # Check connected node names
    connected_nodes = set()
    for r in rels:
        connected_nodes.add(r["source"])
        connected_nodes.add(r["target"])

    assert "Qubit" in connected_nodes
    assert "Superposition" in connected_nodes


def test_index_manager_enforces_zero_isolated_nodes(tmp_path):
    """Test that Stage 7 index_manager connects isolated nodes in graph.json."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir(parents=True)

    # Create dummy markdown files
    (wiki_dir / "Alpha.md").write_text("# Alpha\n\n## Overview\nAlpha entity", encoding="utf-8")
    (wiki_dir / "Beta.md").write_text("# Beta\n\n## Overview\nBeta entity", encoding="utf-8")
    (wiki_dir / "Gamma.md").write_text("# Gamma\n\n## Overview\nGamma entity", encoding="utf-8")

    page_records = [
        {"entity_name": "Alpha", "filename": "Alpha.md", "entity_type": "CONCEPT"},
        {"entity_name": "Beta", "filename": "Beta.md", "entity_type": "CONCEPT"},
        {"entity_name": "Gamma", "filename": "Gamma.md", "entity_type": "CONCEPT"},
    ]

    # Empty initial relationships
    relationships = []

    res = update_wiki_index_catalog(str(wiki_dir), page_records, relationships)

    import json
    graph_data = json.loads((wiki_dir / "graph.json").read_text(encoding="utf-8"))

    nodes = graph_data["nodes"]
    edges = graph_data["edges"]

    assert len(nodes) == 3
    assert len(edges) >= 2

    # Calculate degree for each node
    degrees = {n["id"]: 0 for n in nodes}
    for e in edges:
        if e["source"] in degrees:
            degrees[e["source"]] += 1
        if e["target"] in degrees:
            degrees[e["target"]] += 1

    # Verify EVERY node has degree >= 1
    for node_id, degree in degrees.items():
        assert degree >= 1, f"Node {node_id} is isolated with degree 0!"


def test_wiki_engine_creates_connected_relationships(tmp_path):
    """Test that wiki engine creates at least 1 relationship for every generated page."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir(parents=True)

    knowledge_json = {
        "entities": [
            {"name": "Entity Standalone", "type": "CONCEPT", "description": "Standalone entity"}
        ],
        "concepts": [],
        "relationships": [],
        "facts": []
    }

    res = update_or_create_wiki_pages(knowledge_json, "test_doc.txt", str(wiki_dir))

    page_rec = res["page_records"][0]
    assert len(page_rec["relationships"]) >= 1
    assert "Entity Standalone" in page_rec["content"]
    assert "Knowledge Graph Relationships" in page_rec["content"]


def test_person_author_wiki_page_generation(tmp_path):
    """Test that uploading a CV generates a dedicated Wiki page for the person/candidate name."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir(parents=True)

    knowledge_json = {
        "title": "Jayashan Manodya Resume",
        "people": ["Jayashan Manodya"],
        "authors": ["Jayashan Manodya"],
        "entities": [
            {"name": "WikiLLM Project", "type": "PRODUCT", "description": "AI Wiki RAG Project"},
            {"name": "Glanz Digital", "type": "ORGANIZATION", "description": "Software Company"}
        ],
        "concepts": [],
        "relationships": []
    }

    _enforce_no_isolated_entities(knowledge_json, "Jayashan Manodya.pdf", {})
    res = update_or_create_wiki_pages(knowledge_json, "Jayashan Manodya.pdf", str(wiki_dir))

    page_names = [p["entity_name"] for p in res["page_records"]]
    assert "Jayashan Manodya" in page_names

    # Check that Jayashan_Manodya.md file was created on disk
    person_file = wiki_dir / "Jayashan_Manodya.md"
    assert person_file.exists()
    content = person_file.read_text(encoding="utf-8")
    assert "Jayashan Manodya" in content
    assert "PERSON" in content


def test_exhaustive_wiki_content_preservation(tmp_path):
    """Test that wiki engine preserves full detailed facts, metrics, and un-summarized content."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir(parents=True)

    knowledge_json = {
        "entities": [
            {
                "name": "Automated Room Comfort System",
                "type": "SYSTEM",
                "description": "Comprehensive IoT Room Comfort System with DHT22 temperature sensor operating at 24.5C, relay module 5V, ESP32 microcontroller, and PID loop controller.",
                "aliases": []
            }
        ],
        "concepts": [],
        "relationships": [],
        "facts": [
            {
                "subject": "Automated Room Comfort System",
                "statement": "Operates at 24.5C temperature threshold with 60% relative humidity using DHT22 pin 4.",
                "provenance": "Section 3.1 Hardware Specifications"
            }
        ]
    }

    res = update_or_create_wiki_pages(knowledge_json, "room_comfort.pdf", str(wiki_dir))
    page_rec = res["page_records"][0]
    
    assert "DHT22" in page_rec["content"]
    assert "24.5C" in page_rec["content"]
    assert "Section 3.1 Hardware Specifications" in page_rec["content"]


