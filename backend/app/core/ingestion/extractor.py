"""Stage 5: Knowledge Extraction Engine.

Performs deep structured knowledge extraction from cleaned markdown and enrichment metadata.
NEVER generates wiki pages directly from raw text.
Produces structured JSON containing:
- entities
- concepts
- relationships
- facts
- claims
- evidence
- contradictions
- timelines
- events
- definitions
- comparisons
before wiki page generation or updating.
"""

import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from ..llm.factory import create_chat_model


KNOWLEDGE_EXTRACTION_PROMPT = """You are an expert Knowledge Graph Extraction and Ontology Engineer.
Your task is to analyze document text and enriched metadata to extract formal knowledge items into structured JSON.

CRITICAL INSTRUCTIONS FOR ACCURATE LLM RETRIEVAL:
1. DO NOT SUMMARIZE AWAY SPECIFIC DETAILS. Extract EVERY numeric value, GPA, credit count, registration/ID number, date, grade, affiliation, score, module name, and specific claim present in the document.
2. For each entity, the `description` MUST be a comprehensive, in-depth multi-paragraph overview detailing full background context, qualifications, achievements, affiliations, and attributes strictly based on the text.
3. Extract an EXHAUSTIVE list of `facts` (at least 5 to 25 detailed bullet statements per entity if available in text). Every fact should state explicit numbers, dates, and attributes.

Extract ONLY structured knowledge objects according to this exact JSON schema:

{
  "entities": [
    {
      "name": "Entity Full Name or Title",
      "type": "ORGANIZATION | PERSON | LOCATION | PRODUCT | CONCEPT | EVENT | SYSTEM | TECHNOLOGY",
      "description": "Comprehensive, highly detailed multi-paragraph overview with full context and background details.",
      "aliases": ["Alias 1", "Abbreviation 1"]
    }
  ],
  "concepts": [
    {
      "name": "Concept Name",
      "definition": "Detailed conceptual definition explaining key principles",
      "domain": "Domain or context"
    }
  ],
  "relationships": [
    {
      "source": "Subject Entity/Concept",
      "relation": "RELATION_TYPE (e.g. ENROLLED_IN, SPECIALIZES_IN, FOUNDED_BY, PRODUCES, APPLIES_TO, PART_OF, CREATED, USES)",
      "target": "Object Entity/Concept",
      "evidence": "Quoted line or textual evidence supporting relationship"
    }
  ],
  "facts": [
    {
      "subject": "Subject name",
      "statement": "Granular factual statement with exact numbers/metrics/dates",
      "confidence": 0.95
    }
  ],
  "claims": [
    {
      "claim": "Claim text",
      "source_reference": "Document section/citation reference",
      "evidence": "Exact quoted evidence supporting claim"
    }
  ],
  "timelines": [
    {
      "date_or_period": "YYYY or Period description",
      "event_title": "Event title",
      "description": "Exhaustive event detail"
    }
  ],
  "events": [
    {
      "event_name": "Event name",
      "participants": ["Entity 1", "Entity 2"],
      "description": "Detailed event description"
    }
  ],
  "definitions": [
    {
      "term": "Term",
      "definition": "Comprehensive definition"
    }
  ],
  "comparisons": [
    {
      "subject_a": "Subject A",
      "subject_b": "Subject B",
      "comparison_aspect": "Aspect being compared",
      "finding": "Detailed comparison conclusion"
    }
  ],
  "contradictions": [
    {
      "subject": "Topic or Entity",
      "conflicting_statement_a": "First statement",
      "conflicting_statement_b": "Second conflicting statement",
      "explanation": "Why statements conflict"
    }
  ]
}

Return ONLY valid JSON. No markdown code blocks, no preamble, no trailing text.
"""


def extract_structured_knowledge(
    cleaned_markdown: str,
    enrichment_metadata: Dict[str, Any],
    filename: str,
    existing_wiki_context: Optional[str] = None
) -> Dict[str, Any]:
    """Perform Stage 5 Knowledge Extraction into structured JSON.

    Args:
        cleaned_markdown: Cleaned document markdown.
        enrichment_metadata: Structured metadata from Stage 4.
        filename: Original filename.
        existing_wiki_context: Optional summary of existing wiki pages for contradiction detection.

    Returns:
        Dict adhering to Stage 5 knowledge schema.
    """
    if not cleaned_markdown.strip():
        return _fallback_knowledge_extraction(filename, enrichment_metadata)

    llm = create_chat_model()
    truncated_md = cleaned_markdown[:15000]

    context_prompt = f"Source Document: {filename}\n"
    if existing_wiki_context:
        context_prompt += f"\nExisting Wiki Context (Check for contradictions):\n{existing_wiki_context[:3000]}\n"

    context_prompt += f"\nDocument Text:\n{truncated_md}"

    messages = [
        SystemMessage(content=KNOWLEDGE_EXTRACTION_PROMPT),
        HumanMessage(content=context_prompt)
    ]

    try:
        response = llm.invoke(messages)
        res_text = response.content.strip()
        if res_text.startswith("```"):
            res_text = res_text.split("```", 2)[1]
            if res_text.startswith("json"):
                res_text = res_text[4:].strip()
            res_text = res_text.rstrip("`").strip()

        knowledge_json = json.loads(res_text)
    except Exception:
        knowledge_json = _fallback_knowledge_extraction(filename, enrichment_metadata)

    # Ensure required arrays are present
    required_keys = ["entities", "concepts", "relationships", "facts", "claims", "timelines", "events", "definitions", "comparisons", "contradictions"]
    for k in required_keys:
        if k not in knowledge_json or not isinstance(knowledge_json[k], list):
            knowledge_json[k] = []

    return knowledge_json


def _fallback_knowledge_extraction(filename: str, enrichment: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback structured knowledge when extraction fails."""
    title = enrichment.get("title", filename)
    concepts = enrichment.get("concepts", [title])

    entities = [{
        "name": title,
        "type": "DOCUMENT",
        "description": enrichment.get("executive_summary", f"Document entity for {filename}"),
        "aliases": []
    }]

    for concept in concepts[:5]:
        if concept != title:
            entities.append({
                "name": concept,
                "type": "CONCEPT",
                "description": f"Concept extracted from {filename}",
                "aliases": []
            })

    return {
        "entities": entities,
        "concepts": [{"name": c, "definition": f"Concept in {filename}", "domain": "General"} for c in concepts[:5]],
        "relationships": [],
        "facts": [{"subject": title, "statement": f"Document {filename} ingested.", "confidence": 1.0}],
        "claims": [],
        "timelines": [],
        "events": [],
        "definitions": [],
        "comparisons": [],
        "contradictions": []
    }
