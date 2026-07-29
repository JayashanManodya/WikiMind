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


ENRICHMENT_SYSTEM_PROMPT = """You are an expert Document Intelligence and Metadata Extraction Agent.
Your task is to analyze document text and generate comprehensive, highly detailed structured metadata and summaries without omitting any specific facts or figures.

Analyze the document carefully and return ONLY a valid JSON object with the following fields:
1. `title`: Full title of the document or infer an appropriate descriptive title.
2. `authors`: List of authors (strings) or empty array if unknown.
3. `publication_date`: Date or year of publication if mentioned, or null.
4. `organisations`: List of organization/company names mentioned.
5. `people`: List of key individuals/people mentioned.
6. `locations`: List of geographical places, countries, cities mentioned.
7. `products`: List of products, systems, technologies, software, or services mentioned.
8. `concepts`: List of core domain concepts/topics.
9. `keywords`: List of 5-15 searchable keywords.
10. `citations`: List of citations/external references found in document.
11. `references`: List of reference titles or links in document.
12. `executive_summary`: Rich, detailed overview of the document preserving all key facts, achievements, background, and specific metrics.
13. `section_summaries`: Array of objects `[{"section_title": "...", "summary": "..."}]` giving comprehensive summaries for each section.
14. `important_facts`: Exhaustive list of key factual statements/takeaways. Include every specific score, credit count, GPA, ID number, and date mentioned.
15. `glossary_terms`: Array of objects `[{"term": "...", "definition": "..."}]`.

Strict JSON output only. No markdown formatting, no commentary.
"""


def enrich_document(
    cleaned_markdown: str,
    filename: str,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Perform Stage 4 content enrichment on cleaned document markdown.

    Args:
        cleaned_markdown: Cleaned markdown text from Stage 3.
        filename: Document filename.
        output_dir: Optional path to store separate metadata JSON file.

    Returns:
        Dict containing structured metadata and summaries.
    """
    if not cleaned_markdown.strip():
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
