"""Wiki page generator: transforms cleaned document text into structured Wiki Markdown (.md) pages with explicit Knowledge Graph relationships."""

import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from ..llm.factory import create_chat_model


WIKI_SYSTEM_PROMPT = """You are an expert Knowledge Graph & Wiki Engineer.
Your task is to analyze document text and extract structured Wiki Knowledge Pages and explicit entity-relationship triples.

For each entity/topic, generate a JSON object with:
1. `entity_name`: Short title for the entity/topic (e.g. "Tesla", "Electric Vehicles", "Elon Musk").
2. `entity_type`: Classification like "CONCEPT", "ORGANIZATION", "PERSON", "TECHNOLOGY", "EVENT", or "TOPIC".
3. `overview`: Comprehensive, clear summary of what this entity/topic is based strictly on the text.
4. `key_facts`: List of clear fact bullet points. Include confidence estimates if helpful (e.g. "Fact text (Confidence: 0.95)").
5. `related_entities`: List of related entity names mentioned in the text.
6. `relationships`: List of typed relationship objects: `{"source": "Entity A", "relation": "RELATION_NAME", "target": "Entity B"}`.

Respond ONLY with a valid JSON array of objects representing the extracted Wiki pages.
Example JSON:
[
  {
    "entity_name": "Tesla",
    "entity_type": "ORGANIZATION",
    "overview": "Tesla is an American electric vehicle and clean energy company founded in 2003 by Elon Musk.",
    "key_facts": [
      "Founded by Elon Musk in 2003 (Confidence: 0.95)",
      "Produces electric vehicles and battery energy storage (Confidence: 0.95)"
    ],
    "related_entities": ["Elon Musk", "Electric Vehicles"],
    "relationships": [
      {"source": "Tesla", "relation": "FOUNDED_BY", "target": "Elon Musk"},
      {"source": "Tesla", "relation": "PRODUCES", "target": "Electric Vehicles"}
    ]
  }
]
"""


def generate_wiki_pages_from_text(cleaned_text: str, filename: str, wiki_dir: str = "wiki") -> List[Dict[str, Any]]:
    """Transform cleaned text into Wiki Markdown files with explicit relationships, saving them to disk and updating index.json.

    Args:
        cleaned_text: Cleaned plain text of the document.
        filename: Original source document filename.
        wiki_dir: Directory where markdown files and index.json are saved.

    Returns:
        List of generated wiki page dicts.
    """
    if not cleaned_text.strip():
        entity_name = Path(filename).stem
        return [_create_fallback_wiki_page(entity_name, filename, cleaned_text, wiki_dir)]

    llm = create_chat_model()
    prompt = f"Source Document: {filename}\n\nDocument Text:\n{cleaned_text[:12000]}"
    
    messages = [
        SystemMessage(content=WIKI_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]

    try:
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        # Strip markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```", 2)[1]
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
            response_text = response_text.rstrip("`").strip()

        wiki_data = json.loads(response_text)
    except Exception:
        entity_name = Path(filename).stem.replace("_", " ").title()
        return [_create_fallback_wiki_page(entity_name, filename, cleaned_text, wiki_dir)]

    if not isinstance(wiki_data, list):
        wiki_data = [wiki_data]

    generated_pages = []
    target_dir = Path(wiki_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    today_str = datetime.date.today().isoformat()
    all_extracted_relationships = []

    for item in wiki_data:
        entity_name = item.get("entity_name", "Topic").strip()
        entity_type = item.get("entity_type", "CONCEPT").strip().upper()
        overview = item.get("overview", "").strip()
        key_facts = item.get("key_facts", [])
        related = item.get("related_entities", [])
        relationships = item.get("relationships", [])

        # Format Markdown content
        md_filename = f"{entity_name.replace(' ', '_').replace('/', '_')}.md"
        
        facts_md = "\n".join(f"- {fact}" for fact in key_facts) if key_facts else "- No facts listed."
        related_md = ", ".join(f"[[{r}]]" for r in related) if related else "None"
        
        rel_lines = []
        for rel in relationships:
            src = rel.get("source", entity_name)
            rel_type = rel.get("relation", "RELATED_TO")
            tgt = rel.get("target", "")
            if tgt:
                rel_lines.append(f"- [[{src}]] --[`{rel_type}`]--> [[{tgt}]]")
                all_extracted_relationships.append({"source": src, "relation": rel_type, "target": tgt})
        
        rel_md = "\n".join(rel_lines) if rel_lines else "- No explicit relationships defined."

        md_content = f"""# {entity_name}

**Entity Type**: `{entity_type}`  
**Last Updated**: `{today_str}`

## Overview
{overview}

## Key Facts
{facts_md}

## Related Entities
{related_md}

## Knowledge Graph Relationships
{rel_md}

## Document Sources
- [{filename}](file://{filename})
"""

        # Save .md file
        md_path = target_dir / md_filename
        md_path.write_text(md_content, encoding="utf-8")

        page_record = {
            "entity_name": entity_name,
            "filename": md_filename,
            "entity_type": entity_type,
            "related_entities": related,
            "relationships": relationships,
            "content": md_content,
            "path": str(md_path)
        }
        generated_pages.append(page_record)

    # Update index.json and graph.json
    _update_wiki_index(target_dir, generated_pages, all_extracted_relationships)

    return generated_pages


def _create_fallback_wiki_page(entity_name: str, filename: str, text: str, wiki_dir: str) -> Dict[str, Any]:
    """Create a single fallback Wiki page when extraction fails or is empty."""
    target_dir = Path(wiki_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    today_str = datetime.date.today().isoformat()
    md_filename = f"{entity_name.replace(' ', '_')}.md"
    overview = text[:1000] if text else "No content available."

    md_content = f"""# {entity_name}

**Entity Type**: `DOCUMENT`  
**Last Updated**: `{today_str}`

## Overview
{overview}

## Knowledge Graph Relationships
- No explicit relationships defined.

## Document Sources
- [{filename}](file://{filename})
"""
    md_path = target_dir / md_filename
    md_path.write_text(md_content, encoding="utf-8")

    page_record = {
        "entity_name": entity_name,
        "filename": md_filename,
        "entity_type": "DOCUMENT",
        "related_entities": [],
        "relationships": [],
        "content": md_content,
        "path": str(md_path)
    }

    _update_wiki_index(target_dir, [page_record], [])
    return page_record


def _update_wiki_index(wiki_dir: Path, new_pages: List[Dict[str, Any]], new_relationships: List[Dict[str, Any]]):
    """Update index.json catalog, graph.json, and Index.md overview in wiki_dir."""
    index_file = wiki_dir / "index.json"
    graph_file = wiki_dir / "graph.json"

    existing_pages = []
    existing_edges = []

    if index_file.exists():
        try:
            data = json.loads(index_file.read_text(encoding="utf-8"))
            existing_pages = data.get("pages", [])
            existing_edges = data.get("graph", {}).get("edges", [])
        except Exception:
            existing_pages = []

    page_map = {p["entity_name"]: p for p in existing_pages}
    
    today_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for p in new_pages:
        page_map[p["entity_name"]] = {
            "entity_name": p["entity_name"],
            "filename": p["filename"],
            "entity_type": p["entity_type"],
            "related_entities": p.get("related_entities", []),
            "updated_at": today_str
        }

    all_pages = list(page_map.values())

    # Build unique graph edges
    edge_set = set()
    all_edges = []
    for edge in existing_edges + new_relationships:
        key = (edge.get("source"), edge.get("relation"), edge.get("target"))
        if key not in edge_set and key[0] and key[2]:
            edge_set.add(key)
            all_edges.append({"source": key[0], "relation": key[1], "target": key[2]})

    # Build graph nodes
    nodes = [{"id": p["entity_name"], "label": p["entity_name"], "type": p["entity_type"]} for p in all_pages]

    graph_data = {
        "nodes": nodes,
        "edges": all_edges
    }
    
    index_data = {
        "total_pages": len(all_pages),
        "rebuilt_at": today_str,
        "pages": all_pages,
        "graph": graph_data
    }

    index_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
    graph_file.write_text(json.dumps(graph_data, indent=2), encoding="utf-8")

    # Rebuild Index.md
    index_md = "# Wiki Knowledge Base Index\n\n"
    index_md += f"**Total Wiki Pages**: {len(all_pages)}\n"
    index_md += f"**Total Knowledge Graph Edges**: {len(all_edges)}\n\n"
    for p in all_pages:
        index_md += f"- [{p['entity_name']}](./{p['filename']}) (`{p['entity_type']}`)\n"

    (wiki_dir / "Index.md").write_text(index_md, encoding="utf-8")
