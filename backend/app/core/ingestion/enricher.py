"""Stage 4: Content Enrichment Engine.

Extracts structured document metadata and generates summaries/glossary terms
using LLM reasoning before knowledge extraction.
Produces:
- title, authors, publication date, organisations, people, locations, products, concepts, keywords, citations, references
- executive summary, section summaries, important facts, glossary terms.
Stores metadata separately in JSON format.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from ..llm.factory import create_chat_model


ENRICHMENT_SYSTEM_PROMPT = """You are an expert Document Intelligence and Metadata Extraction Agent operating under a STRICT KNOWLEDGE BOUNDARY.

STRICT RULES:
1. TREAT THE UPLOADED DOCUMENT AS THE PRIMARY SOURCE OF TRUTH.
2. NEVER introduce background history, founding dates, locations, employee counts, or external facts not present in the document.
3. Extract ONLY information that is explicitly stated or can be directly inferred from the document.
4. If information is insufficient or unstated, return empty array `[]` or null. NEVER invent missing details.

Analyze the document carefully and return ONLY a valid JSON object with the following fields:
1. `title`: Title of the document as stated in text or inferred directly from heading.
2. `authors`: List of authors explicitly mentioned, or empty array.
3. `publication_date`: Date or year explicitly mentioned, or null.
4. `organisations`: List of organization names explicitly mentioned.
5. `people`: List of individuals explicitly mentioned.
6. `locations`: List of geographical places explicitly mentioned.
7. `products`: List of products/services explicitly mentioned.
8. `concepts`: List of core domain topics explicitly discussed.
9. `keywords`: List of 5-15 keywords found directly in text.
10. `citations`: List of citations/external links in document.
11. `references`: List of reference titles or links in document.
12. `executive_summary`: Concise summary strictly based on document text.
13. `section_summaries`: Array of objects `[{"section_title": "...", "summary": "..."}]` for sections present in text.
14. `important_facts`: List of key factual statements explicitly stated in document.
15. `glossary_terms`: Array of objects `[{"term": "...", "definition": "..."}]` for terms defined in document.

Strict JSON output only. No markdown formatting, no commentary.
"""


def enrich_document(
    cleaned_markdown: str,
    filename: str,
    output_dir: Optional[str] = None,
    extracted_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Perform Stage 4 content enrichment on cleaned document markdown.
    
    Reuses extracted_data from unified LLM call if provided to avoid latency.

    Args:
        cleaned_markdown: Cleaned markdown text from Stage 3.
        filename: Document filename.
        output_dir: Optional path to store separate metadata JSON file.
        extracted_data: Optional unified extraction JSON from Stage 5.

    Returns:
        Dict containing structured metadata and summaries.
    """
    if extracted_data:
        # Reuse existing metadata fields from unified LLM call
        enrichment_data = {
            "title": extracted_data.get("title", filename),
            "authors": extracted_data.get("authors", []),
            "publication_date": extracted_data.get("publication_date"),
            "organisations": extracted_data.get("organisations", []),
            "people": extracted_data.get("people", []),
            "locations": extracted_data.get("locations", []),
            "products": extracted_data.get("products", []),
            "concepts": [c.get("name") if isinstance(c, dict) else c for c in extracted_data.get("concepts", [])],
            "keywords": extracted_data.get("keywords", []),
            "citations": extracted_data.get("citations", []),
            "references": extracted_data.get("references", []),
            "executive_summary": extracted_data.get("executive_summary", ""),
            "section_summaries": extracted_data.get("section_summaries", []),
            "important_facts": extracted_data.get("important_facts", []),
            "glossary_terms": extracted_data.get("glossary_terms", [])
        }
    elif not cleaned_markdown.strip():
        enrichment_data = _fallback_enrichment(filename, cleaned_markdown)
    else:
        llm = create_chat_model()
        truncated_text = cleaned_markdown[:15000]
        prompt = f"Filename: {filename}\n\nDocument Markdown:\n{truncated_text}"

        messages = [
            SystemMessage(content=ENRICHMENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]

        try:
            response = llm.invoke(messages)
            res_text = response.content.strip()
            if res_text.startswith("```"):
                res_text = res_text.split("```", 2)[1]
                if res_text.startswith("json"):
                    res_text = res_text[4:].strip()
                res_text = res_text.rstrip("`").strip()
            
            enrichment_data = json.loads(res_text)
        except Exception:
            enrichment_data = _fallback_enrichment(filename, cleaned_markdown)

    enrichment_data["filename"] = filename

    # Store metadata separately if output_dir provided
    if output_dir:
        out_path = Path(output_dir) / "metadata"
        out_path.mkdir(parents=True, exist_ok=True)
        meta_file = out_path / f"{Path(filename).stem}_enrichment.json"
        meta_file.write_text(json.dumps(enrichment_data, indent=2), encoding="utf-8")
        enrichment_data["stored_metadata_path"] = str(meta_file.resolve())

    return enrichment_data


def _fallback_enrichment(filename: str, text: str) -> Dict[str, Any]:
    """Fallback enrichment structure when LLM fails or text is minimal."""
    stem = Path(filename).stem.replace("_", " ").title()
    return {
        "title": stem,
        "authors": [],
        "publication_date": None,
        "organisations": [],
        "people": [],
        "locations": [],
        "products": [],
        "concepts": [stem],
        "keywords": [stem.lower()],
        "citations": [],
        "references": [],
        "executive_summary": text[:300] if text else f"Document content for {filename}.",
        "section_summaries": [{"section_title": "Overview", "summary": text[:300]}],
        "important_facts": [],
        "glossary_terms": []
    }
