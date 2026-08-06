"""Structured Ingestion Pipeline Orchestrator.

Implements the complete 8-stage document ingestion pipeline:
- Stage 1: Raw Document Storage
- Stage 2: LlamaParse & Multi-format Parser
- Stage 3: Cleaning & Normalization
- Stage 4: Content Enrichment
- Stage 5: Knowledge Extraction (NEVER generates pages directly from raw text)
- Stage 6: Incremental Wiki Update Engine
- Stage 7: Index Maintenance
- Stage 8: Log Maintenance
"""

from pathlib import Path
from typing import List, Dict, Any

from .raw_storage import store_raw_document
from .llama_parser import parse_with_llamaparse_or_fallback
from .cleaner import clean_and_normalize_markdown
from .extractor import extract_structured_knowledge
from .wiki_engine import update_or_create_wiki_pages
from .index_manager import update_wiki_index_catalog
from .logger_manager import append_ingestion_log


def run_ingestion_pipeline(
    file_bytes: bytes,
    filename: str,
    user_id: str = "default_user",
    wiki_dir: str = "wiki"
) -> Dict[str, Any]:
    """Orchestrate the complete 8-stage WikiLLM structured ingestion pipeline.

    Args:
        file_bytes: Raw binary bytes of uploaded document.
        filename: Original filename.
        user_id: User identifier for isolated storage.
        wiki_dir: User target wiki directory path.

    Returns:
        Dict containing end-to-end pipeline execution details and generated page records.
    """
    # Stage 1 — Raw Document (Immutable Storage)
    raw_doc_record = store_raw_document(
        file_bytes=file_bytes,
        filename=filename,
        user_id=user_id
    )

    # Stage 2 — LlamaParse / Multi-format Structured Parsing
    parsed_output = parse_with_llamaparse_or_fallback(
        file_bytes=file_bytes,
        filename=filename
    )

    # Stage 3 — Cleaning & Normalization
    cleaned_output = clean_and_normalize_markdown(parsed_output)

    # Single-Pass Knowledge Extraction & Metadata Enrichment
    knowledge_json = extract_structured_knowledge(
        cleaned_markdown=cleaned_output["cleaned_markdown"],
        enrichment_metadata={},
        filename=filename
    )

    enrichment_metadata = {
        "filename": filename,
        "title": knowledge_json.get("title", filename),
        "authors": knowledge_json.get("authors", []),
        "publication_date": knowledge_json.get("publication_date"),
        "organisations": knowledge_json.get("organisations", []),
        "people": knowledge_json.get("people", []),
        "locations": knowledge_json.get("locations", []),
        "products": knowledge_json.get("products", []),
        "concepts": [c.get("name") if isinstance(c, dict) else c for c in knowledge_json.get("concepts", [])],
        "keywords": knowledge_json.get("keywords", []),
        "citations": knowledge_json.get("citations", []),
        "references": knowledge_json.get("references", []),
        "executive_summary": knowledge_json.get("executive_summary", ""),
        "section_summaries": knowledge_json.get("section_summaries", []),
        "important_facts": knowledge_json.get("important_facts", []),
        "glossary_terms": knowledge_json.get("glossary_terms", [])
    }

    # Stage 6 — Wiki Update Engine (Incremental update/create pages)
    wiki_update_results = update_or_create_wiki_pages(
        knowledge_json=knowledge_json,
        source_filename=filename,
        wiki_dir=wiki_dir
    )

    # Stage 7 — Index Maintenance (Index.md, index.json, graph.json)
    index_results = update_wiki_index_catalog(
        wiki_dir=wiki_dir,
        page_records=wiki_update_results["page_records"],
        relationships=knowledge_json.get("relationships", [])
    )

    # Stage 8 — Persist into Neo4j Graph DB & Log Maintenance
    from ..graph_db import save_wiki_page
    for rec in wiki_update_results["page_records"]:
        try:
            entity_title = rec.get("entity_name") or rec.get("title", "")
            if entity_title:
                save_wiki_page(
                    user_id=user_id,
                    title=entity_title,
                    summary=rec.get("summary", "") or rec.get("description", ""),
                    content=rec.get("content", ""),
                    category=rec.get("entity_type") or rec.get("category", "General"),
                    file_name=rec.get("filename") or rec.get("file_name", filename),
                    linked_titles=rec.get("related_entities") or rec.get("links", [])
                )
        except Exception as e:
            print(f"Neo4j save wiki page note: {e}")

    num_indexed = len(wiki_update_results["page_records"])

    log_path = append_ingestion_log(
        wiki_dir=wiki_dir,
        document_name=filename,
        wiki_update_results=wiki_update_results,
        knowledge_json=knowledge_json
    )

    return {
        "status": "success",
        "filename": filename,
        "raw_doc_record": raw_doc_record,
        "parsed_output": parsed_output,
        "cleaned_output": cleaned_output,
        "parser_used": parsed_output.get("parser_used", "LlamaParse"),
        "cleaning_stats": cleaned_output.get("cleaning_stats", {}),
        "enrichment_metadata": enrichment_metadata,
        "knowledge_extracted": knowledge_json,
        "wiki_pages": wiki_update_results["page_records"],
        "pages_created": wiki_update_results["pages_created"],
        "pages_updated": wiki_update_results["pages_updated"],
        "index_stats": index_results,
        "log_path": log_path,
        "chunks": num_indexed
    }


def generate_wiki_pages_from_text(
    cleaned_text: str,
    filename: str,
    wiki_dir: str = "wiki"
) -> List[Dict[str, Any]]:
    """Backwards-compatible wrapper for existing calls using plain text.

    Executes Stages 4 through 8 on text.
    """
    file_bytes = cleaned_text.encode("utf-8")
    result = run_ingestion_pipeline(
        file_bytes=file_bytes,
        filename=filename,
        user_id="default_user",
        wiki_dir=wiki_dir
    )
    return result["wiki_pages"]
