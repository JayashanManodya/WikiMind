"""Stage 7: Index Maintenance Engine.

Maintains Index.md, index.json, and graph.json in the user's wiki directory.
Ensures:
- All active wiki pages are listed in strict alphabetical ordering
- Category grouping by entity_type
- Summaries, categories, and tags included
- Dead links (pointing to non-existent markdown files) are pruned
"""

import json
import re
import datetime
from pathlib import Path
from typing import Dict, Any, List


def update_wiki_index_catalog(
    wiki_dir: str,
    page_records: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute Stage 7 Index Maintenance.

    Args:
        wiki_dir: Directory containing user wiki files.
        page_records: Records of newly processed pages.
        relationships: List of relationship dicts.

    Returns:
        Dict with stats on index updates.
    """
    target_dir = Path(wiki_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    index_json_path = target_dir / "index.json"
    graph_json_path = target_dir / "graph.json"
    index_md_path = target_dir / "Index.md"

    # Scan existing markdown files to eliminate dead links
    existing_md_files = {f.name: f for f in target_dir.glob("*.md") if f.name not in ["Index.md", "log.md"]}

    existing_pages = []
    existing_edges = []

    if index_json_path.exists():
        try:
            data = json.loads(index_json_path.read_text(encoding="utf-8"))
            existing_pages = data.get("pages", [])
            existing_edges = data.get("graph", {}).get("edges", [])
        except Exception:
            existing_pages = []

    page_map = {}
    for p in existing_pages:
        # Keep only if corresponding .md file exists on disk (Prune dead links)
        if p.get("filename") in existing_md_files:
            page_map[p["entity_name"]] = p

    today_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Add or update current records
    for pr in page_records:
        entity_name = pr["entity_name"]
        filename = pr["filename"]
        
        # Read summary excerpt from page file if available
        summary_excerpt = ""
        page_path = target_dir / filename
        if page_path.exists():
            content = page_path.read_text(encoding="utf-8")
            match = re.search(r"## Overview\n(.*?)(?=\n## |\Z)", content, flags=re.DOTALL)
            if match:
                summary_excerpt = match.group(1).strip()[:180] + "..."

        page_map[entity_name] = {
            "entity_name": entity_name,
            "filename": filename,
            "entity_type": pr.get("entity_type", "CONCEPT"),
            "summary": summary_excerpt,
            "category": pr.get("entity_type", "CONCEPT").title(),
            "tags": [pr.get("entity_type", "CONCEPT").lower()],
            "related_entities": pr.get("related_entities", []),
            "updated_at": today_iso
        }

    # Sort pages alphabetically by entity_name
    sorted_pages = sorted(list(page_map.values()), key=lambda x: x["entity_name"].lower())

    # Build graph edges
    edge_set = set()
    all_edges = []
    for edge in existing_edges + relationships:
        src = edge.get("source")
        tgt = edge.get("target")
        rel = edge.get("relation", "RELATED_TO")
        if src and tgt and src in page_map and tgt in page_map:
            key = (src, rel, tgt)
            if key not in edge_set:
                edge_set.add(key)
                all_edges.append({"source": src, "relation": rel, "target": tgt})

    nodes = [{"id": p["entity_name"], "label": p["entity_name"], "type": p["entity_type"]} for p in sorted_pages]

    graph_data = {
        "nodes": nodes,
        "edges": all_edges
    }

    index_data = {
        "total_pages": len(sorted_pages),
        "rebuilt_at": today_iso,
        "pages": sorted_pages,
        "graph": graph_data
    }

    # Write JSON catalogs
    index_json_path.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
    graph_json_path.write_text(json.dumps(graph_data, indent=2), encoding="utf-8")

    # Generate Index.md sorted alphabetically and grouped by category
    index_md = "# Wiki Knowledge Base Index\n\n"
    index_md += f"**Total Active Wiki Pages**: {len(sorted_pages)}  \n"
    index_md += f"**Total Knowledge Edges**: {len(all_edges)}  \n"
    index_md += f"**Last Updated**: `{today_iso[:10]}`\n\n"

    # Group by category
    category_map: Dict[str, List[Dict[str, Any]]] = {}
    for p in sorted_pages:
        cat = p.get("category", "General")
        category_map.setdefault(cat, []).append(p)

    for cat in sorted(category_map.keys()):
        index_md += f"## Category: {cat}\n\n"
        for p in category_map[cat]:
            sum_text = f" - *{p['summary']}*" if p.get("summary") else ""
            index_md += f"- [{p['entity_name']}](./{p['filename']}){sum_text}\n"
        index_md += "\n"

    index_md_path.write_text(index_md, encoding="utf-8")

    return {
        "total_pages": len(sorted_pages),
        "total_edges": len(all_edges),
        "index_md_path": str(index_md_path.resolve())
    }
