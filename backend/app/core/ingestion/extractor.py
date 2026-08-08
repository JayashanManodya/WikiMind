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
3. MINIMAL PAGES FOR NAMED ENTITIES: If an entity is mentioned ONLY by name without background details in the document, set `description` to: "Mentioned in uploaded source document without additional background details." DO NOT generate unmentioned history or facts.
4. EVERY FACT, CLAIM, AND RELATIONSHIP MUST INCLUDE SOURCE PROVENANCE: Include section or exact textual quote supporting the statement.
5. EXHAUSTIVE FACTUAL COMPLETENESS (ZERO OMISSION): Extract 100% of all factual statements, metrics, numbers, dates, scores, specifications, procedures, attributes, and claims present in the parsed text without omitting any details. Ground every extracted fact strictly in the document text.

CRITICAL UNIVERSAL KNOWLEDGE GRAPH INTEGRATION RULES:
1. UNIVERSAL DOMAIN AGNOSTICISM: Treat all subjects (technical systems, personal profiles, biographies, research papers, legal documents, financial reports, organizational structures, etc.) equally without domain bias.
2. PRIMARY SUBJECT & ENTITY DISCOVERY: Identify the primary subject(s) or main topic of the document. Extract ALL distinct named entities mentioned in the text (Person, Organization, Location, Product, System, Concept, Event, Technology, Document) into the 'entities' array with accurate entity types.
3. EXPLICIT RELATIONSHIP TRIPLES: Extract ALL relationship triples (`Subject --[RELATION_TYPE]--> Object`) explicitly supported by the text linking entities, attributes, topics, and subjects (e.g. `Entity --[HAS_ATTRIBUTE]--> Value`, `Entity --[PART_OF]--> Parent`, `Person --[AFFILIATED_WITH]--> Organization`, `Entity --[CATEGORIZED_AS]--> Topic`). Ensure NO extracted entity remains completely isolated if text provides a connection.
4. NO LOSS OF SPECIFIC DETAILS: Preserve every numeric value, score, date, metric, affiliation, title, identification code, and specific attribute stated in the text.
5. EXHAUSTIVE ENTITY DESCRIPTIONS: For each primary entity with rich text, provide a comprehensive, multi-paragraph overview detailing its background context, attributes, features, responsibilities, or properties strictly grounded in the document text.
6. CANONICAL ENTITY DEDUPLICATION: Use consistent, canonical Title-Case names for all entities across 'entities', 'concepts', 'projects', 'products', 'people', 'organisations', 'locations', and 'relationships'. NEVER output duplicate variations of the same name. Consolidate all facts and relations under one unified canonical title.

Extract ONLY structured metadata and knowledge objects according to this exact JSON schema:

{
  "title": "Title of document as stated or inferred directly from main heading",
  "authors": ["Author 1"],
  "publication_date": "YYYY-MM-DD or year if mentioned, else null",
  "organisations": ["Org 1"],
  "people": ["Person 1"],
  "locations": ["Location 1"],
  "products": ["Product 1"],
  "projects": ["Project 1"],
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
      "relation": "RELATION_TYPE (e.g. HAS_ATTRIBUTE, PART_OF, AFFILIATED_WITH, CATEGORIZED_AS, LOCATED_IN, DEPENDS_ON, ASSOCIATED_WITH)",
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
        SystemMessage(content=UNIFIED_ENRICHMENT_EXTRACTION_PROMPT),
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
    """Post-processing step guaranteeing that 100% of all extracted entities form a single,
    unified connected Knowledge Graph component centered around the document's primary subject.
    Eliminates all floating disconnected sub-graph islands.
    """
    entities = knowledge_json.get("entities", [])
    concepts = knowledge_json.get("concepts", [])
    relationships = knowledge_json.get("relationships", [])

    # Collect all real extracted node names
    all_node_names = []
    for ent in entities:
        n = ent.get("name", "").strip()
        if n and n not in all_node_names:
            all_node_names.append(n)
    for conc in concepts:
        c = conc.get("name", "").strip() if isinstance(conc, dict) else str(conc).strip()
        if c and c not in all_node_names:
            all_node_names.append(c)

    if not all_node_names:
        return

    # Determine primary subject hub (prefer PERSON type entity, else first entity)
    target_hub = all_node_names[0]
    for ent in entities:
        if ent.get("type", "").upper() == "PERSON":
            target_hub = ent.get("name", "").strip()
            break

    # Build undirected adjacency list for graph component reachability
    from collections import defaultdict
    adj = defaultdict(set)
    for rel in relationships:
        s = rel.get("source", "").strip()
        t = rel.get("target", "").strip()
        if s and t:
            adj[s].add(t)
            adj[t].add(s)

    # Perform BFS from target_hub to find all reachable nodes
    reachable = set()
    queue = [target_hub]
    reachable.add(target_hub)
    while queue:
        curr = queue.pop(0)
        for neighbor in adj[curr]:
            if neighbor not in reachable:
                reachable.add(neighbor)
                queue.append(neighbor)

    # For any node or sub-graph island not reachable from target_hub, connect it to target_hub
    for node in all_node_names:
        if node not in reachable:
            if node != target_hub:
                relationships.append({
                    "source": node,
                    "relation": "ASSOCIATED_WITH",
                    "target": target_hub,
                    "evidence": f"Extracted entity from source document {filename}"
                })
                # Update reachability so all nodes in its sub-component are now reachable
                sub_queue = [node]
                reachable.add(node)
                while sub_queue:
                    sub_curr = sub_queue.pop(0)
                    for neighbor in adj[sub_curr]:
                        if neighbor not in reachable:
                            reachable.add(neighbor)
                            sub_queue.append(neighbor)

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
