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


UNIFIED_ENRICHMENT_EXTRACTION_PROMPT = """You are an expert Document Intelligence, Metadata Enrichment, and Knowledge Graph Extraction Engineer operating under a STRICT KNOWLEDGE BOUNDARY.

STRICT KNOWLEDGE BOUNDARY RULES (SOURCE GROUNDING):
1. THE UPLOADED DOCUMENT IS THE ONLY SOURCE OF TRUTH. NEVER use your internal pre-trained knowledge to expand background history, founding dates, locations, employee counts, or facts not present in the text.
2. EXTRACT ONLY WHAT IS EXPLICITLY STATED OR DIRECTLY INFERRED FROM THE TEXT. If a fact, statistic, or date is not in the text, DO NOT INCLUDE IT.
3. MINIMAL PAGES FOR NAMED ENTITIES: If an entity is mentioned ONLY by name (e.g. "SLIIT" or "Elon Musk") without background details in the document, set `description` to: "Mentioned in uploaded source document without additional background details." DO NOT generate unmentioned history or facts.
4. EVERY FACT, CLAIM, AND RELATIONSHIP MUST INCLUDE SOURCE PROVENANCE: Include section or exact textual quote supporting the statement.
5. ACCURACY IS MORE IMPORTANT THAN COMPLETENESS. Prefer sparse, 100% accurate extraction over detailed extraction containing unverified assumptions.

CRITICAL GRAPH & KNOWLEDGE INTEGRATION RULES:
1. NO ENTITY SHOULD REMAIN ISOLATED. Every entity extracted MUST have at least one explicit relationship connecting it to the main domain topic, country, founder, technology, or category strictly supported by text.
2. ALWAYS EXTRACT THE MAIN UMBRELLA DOMAIN CONCEPT (e.g. "Electric Vehicles", "Artificial Intelligence", "Information Technology", "Renewable Energy"). Ensure this main domain concept is included in `concepts` and `entities`.
3. EXTRACT ALL RELATIONSHIP TRIPLES connecting entities explicitly found in text:
   - Entity -> Main Domain Topic (e.g., `Tesla --[CATEGORIZED_AS]--> Electric Vehicles`)
   - Entity -> Location/Country (e.g., `Tesla --[HEADQUARTERED_IN]--> United States`)
   - Entity -> Product/Model (e.g., `Tesla --[MANUFACTURES]--> Tesla Model 3`)
   - Entity -> Technology (e.g., `Tesla --[USES_TECHNOLOGY]--> Autopilot`)
   - Entity -> Founder/Leader (e.g., `Tesla --[FOUNDED_BY]--> Martin Eberhard`)
4. DO NOT SUMMARIZE AWAY SPECIFIC DETAILS. Extract EVERY numeric value, GPA, credit count, registration/ID number, date, grade, affiliation, score, module name, and specific claim present in the document.
5. For each entity with rich document text, the `description` MUST be a comprehensive, in-depth multi-paragraph overview detailing full background context, qualifications, achievements, affiliations, and attributes strictly based on the text.
6. ALWAYS EXTRACT THE PRIMARY SUBJECT / PERSON / AUTHOR / CANDIDATE NAME OF THE DOCUMENT (such as the person whose Resume/CV this is) AND INCLUDE THEM IN `entities` AS TYPE `PERSON` with a full description of their profile, skills, and qualifications. Ensure all projects, experience, education, and affiliations explicitly link to this primary person.
7. NEVER SUMMARIZE OR SHORTEN CONTENT. For each entity, extract exhaustive, complete, un-truncated multi-paragraph narratives containing ALL facts, step-by-step procedures, technical specifications, code snippets, hardware/software details, numbers, dates, and specific statements from the text. DO NOT condense rich document details into high-level generic bullet points.

Extract ONLY structured metadata and knowledge objects according to this exact JSON schema:

{
  "title": "Title of document as stated or inferred directly from main heading",
  "authors": ["Author 1"],
  "publication_date": "YYYY-MM-DD or year if mentioned, else null",
  "organisations": ["Org 1"],
  "people": ["Person 1"],
  "locations": ["Location 1"],
  "products": ["Product 1"],
  "keywords": ["Keyword 1"],
  "citations": ["Citation 1"],
  "references": ["Reference 1"],
  "executive_summary": "Concise executive summary strictly based on document text",
  "section_summaries": [
    {
      "section_title": "Section Title",
      "summary": "Strictly source-grounded section summary"
    }
  ],
  "important_facts": [
    "Key factual statement strictly stated in document text"
  ],
  "glossary_terms": [
    {
      "term": "Term",
      "definition": "Definition explicitly provided in text"
    }
  ],
  "entities": [
    {
      "name": "Entity Full Name or Title",
      "type": "ORGANIZATION | PERSON | LOCATION | PRODUCT | CONCEPT | EVENT | SYSTEM | TECHNOLOGY",
      "description": "Comprehensive multi-paragraph overview strictly grounded in text, OR 'Mentioned in uploaded source document without additional background details.' if only mentioned by name.",
      "aliases": ["Alias 1"]
    }
  ],
  "concepts": [
    {
      "name": "Umbrella Concept or Domain Topic Name",
      "definition": "Detailed conceptual definition strictly based on document text",
      "domain": "Domain context mentioned in document"
    }
  ],
  "relationships": [
    {
      "source": "Subject Entity/Concept",
      "relation": "RELATION_TYPE (e.g. CATEGORIZED_AS, ENROLLED_IN, SPECIALIZES_IN, HEADQUARTERED_IN, MANUFACTURES, FOUNDED_BY, PRODUCES, APPLIES_TO, PART_OF, CREATED, USES_TECHNOLOGY)",
      "target": "Object Entity/Concept",
      "evidence": "Exact quoted textual evidence supporting relationship"
    }
  ],
  "facts": [
    {
      "subject": "Subject name",
      "statement": "Granular factual statement strictly stated in text (preserving exact numbers/metrics/dates)",
      "provenance": "Section title or context sentence",
      "confidence": 1.0
    }
  ],
  "claims": [
    {
      "claim": "Claim text explicitly in text",
      "source_reference": "Section or paragraph reference",
      "evidence": "Exact quoted evidence"
    }
  ],
  "timelines": [
    {
      "date_or_period": "Date or period explicitly in text",
      "event_title": "Event title",
      "description": "Event detail from text"
    }
  ],
  "events": [
    {
      "event_name": "Event name in text",
      "participants": ["Entity 1"],
      "description": "Event detail from text"
    }
  ],
  "definitions": [
    {
      "term": "Term in text",
      "definition": "Definition explicitly provided in text"
    }
  ],
  "comparisons": [
    {
      "subject_a": "Subject A",
      "subject_b": "Subject B",
      "comparison_aspect": "Aspect",
      "finding": "Comparison conclusion explicitly stated"
    }
  ],
  "contradictions": [
    {
      "subject": "Topic or Entity",
      "conflicting_statement_a": "First statement in text",
      "conflicting_statement_b": "Second statement in text",
      "explanation": "Why statements conflict based strictly on text"
    }
  ]
}

Return ONLY valid JSON. No markdown code blocks, no preamble, no trailing text.
"""

KNOWLEDGE_EXTRACTION_PROMPT = UNIFIED_ENRICHMENT_EXTRACTION_PROMPT


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
    truncated_md = cleaned_markdown[:100000]

    context_prompt = f"Source Document: {filename}\n"
    if existing_wiki_context:
        context_prompt += f"\nExisting Wiki Context (Check for contradictions):\n{existing_wiki_context[:10000]}\n"

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

    # Enforce graph connectivity: no entity or concept remains isolated
    _enforce_no_isolated_entities(knowledge_json, filename, enrichment_metadata)

    return knowledge_json


def _enforce_no_isolated_entities(knowledge_json: Dict[str, Any], filename: str, enrichment: Dict[str, Any]):
    """Post-processing step guaranteeing every extracted entity/concept has at least 1 relationship triple
    and registering any document person/author (such as CV candidate) as a primary PERSON entity.
    """
    entities = knowledge_json.get("entities", [])
    concepts = knowledge_json.get("concepts", [])
    relationships = knowledge_json.get("relationships", [])

    # Register people and authors as PERSON entities if not present
    people = knowledge_json.get("people", []) + knowledge_json.get("authors", [])
    existing_entity_names = [e.get("name", "").strip() for e in entities if e.get("name")]
    
    person_hub_name = None
    for person in people:
        p_name = person.strip()
        if p_name and p_name.lower() not in [n.lower() for n in existing_entity_names]:
            entities.append({
                "name": p_name,
                "type": "PERSON",
                "description": f"Primary subject/person extracted from {filename}.",
                "aliases": []
            })
            existing_entity_names.append(p_name)
            if not person_hub_name:
                person_hub_name = p_name
        elif p_name and not person_hub_name:
            person_hub_name = p_name

    # Determine primary hub entity (PERSON > Document title > main concept > first entity)
    doc_stem = filename.replace("_", " ").split(".")[0].title()
    primary_hub = person_hub_name or knowledge_json.get("title") or enrichment.get("title") or doc_stem

    # Collect all node names
    all_node_names = []
    for ent in entities:
        n = ent.get("name", "").strip()
        if n and n not in all_node_names:
            all_node_names.append(n)
    for conc in concepts:
        c = conc.get("name", "").strip()
        if c and c not in all_node_names:
            all_node_names.append(c)

    if not all_node_names:
        return

    # Find connected nodes
    connected_nodes = set()
    for rel in relationships:
        s = rel.get("source", "").strip()
        t = rel.get("target", "").strip()
        if s:
            connected_nodes.add(s)
        if t:
            connected_nodes.add(t)

    # Main target to connect isolated nodes to
    target_hub = primary_hub if primary_hub in all_node_names else all_node_names[0]

    for node in all_node_names:
        if node not in connected_nodes:
            if node != target_hub:
                relationships.append({
                    "source": node,
                    "relation": "MENTIONED_IN",
                    "target": target_hub,
                    "evidence": f"Extracted entity from source document {filename}"
                })
                connected_nodes.add(node)
                connected_nodes.add(target_hub)

    knowledge_json["relationships"] = relationships


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

    relationships = []

    for concept in concepts[:5]:
        if concept != title:
            entities.append({
                "name": concept,
                "type": "CONCEPT",
                "description": f"Concept extracted from {filename}",
                "aliases": []
            })
            relationships.append({
                "source": concept,
                "relation": "PART_OF",
                "target": title,
                "evidence": f"Concept extracted from {filename}"
            })

    return {
        "entities": entities,
        "concepts": [{"name": c, "definition": f"Concept in {filename}", "domain": "General"} for c in concepts[:5]],
        "relationships": relationships,
        "facts": [{"subject": title, "statement": f"Document {filename} ingested.", "confidence": 1.0}],
        "claims": [],
        "timelines": [],
        "events": [],
        "definitions": [],
        "comparisons": [],
        "contradictions": []
    }
