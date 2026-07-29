"""Stage 6: Wiki Update Engine.

Incrementally updates or creates Wiki Markdown pages based on extracted knowledge.
Never rebuilds the wiki from scratch.
Loads existing wiki pages first, merges new knowledge, preserves previous citations,
adds new source document citations, flags contradictions explicitly, and updates
backlinks and related entity cross-references.
"""

import os
import re
import datetime
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple


def update_or_create_wiki_pages(
    knowledge_json: Dict[str, Any],
    source_filename: str,
    wiki_dir: str
) -> Dict[str, Any]:
    """Execute Stage 6 incremental wiki page generation and updates.

    Args:
        knowledge_json: Structured JSON output from Stage 5 knowledge extraction.
        source_filename: Original filename of the source document.
        wiki_dir: User's wiki directory path.

    Returns:
        Dict containing:
            - pages_created: List of created entity page names
            - pages_updated: List of updated entity page names
            - total_affected: Total count of created and updated pages
            - page_records: List of page record dicts
            - contradictions_flagged: List of contradictions logged
    """
    target_dir = Path(wiki_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    today_str = datetime.date.today().isoformat()

    entities = knowledge_json.get("entities", [])
    concepts = knowledge_json.get("concepts", [])
    relationships = knowledge_json.get("relationships", [])
    facts = knowledge_json.get("facts", [])
    claims = knowledge_json.get("claims", [])
    timelines = knowledge_json.get("timelines", [])
    events = knowledge_json.get("events", [])
    definitions = knowledge_json.get("definitions", [])
    comparisons = knowledge_json.get("comparisons", [])
    contradictions = knowledge_json.get("contradictions", [])

    pages_created = []
    pages_updated = []
    page_records = []

    # Map relationships by entity name
    rel_map: Dict[str, List[Dict[str, str]]] = {}
    for rel in relationships:
        src = rel.get("source", "").strip()
        tgt = rel.get("target", "").strip()
        rel_type = rel.get("relation", "RELATED_TO").strip()
        if src:
            rel_map.setdefault(src, []).append({"source": src, "relation": rel_type, "target": tgt})
        if tgt and tgt != src:
            rel_map.setdefault(tgt, []).append({"source": src, "relation": rel_type, "target": tgt})

    # Group entity targets
    all_entity_targets = {}
    for ent in entities:
        name = ent.get("name", "").strip()
        if name:
            all_entity_targets[name] = {
                "entity_name": name,
                "entity_type": ent.get("type", "CONCEPT").strip().upper(),
                "description": ent.get("description", "").strip(),
                "aliases": ent.get("aliases", [])
            }

    # Ensure concepts without entity records are included
    for conc in concepts:
        c_name = conc.get("name", "").strip()
        if c_name and c_name not in all_entity_targets:
            all_entity_targets[c_name] = {
                "entity_name": c_name,
                "entity_type": "CONCEPT",
                "description": conc.get("definition", "").strip(),
                "aliases": []
            }

    # Ensure document people and authors (e.g. CV candidates) are registered as PERSON entities
    people = knowledge_json.get("people", []) + knowledge_json.get("authors", [])
    for p in people:
        p_name = p.strip() if isinstance(p, str) else ""
        if p_name and p_name not in all_entity_targets:
            all_entity_targets[p_name] = {
                "entity_name": p_name,
                "entity_type": "PERSON",
                "description": f"Primary subject/person extracted from source document {source_filename}.",
                "aliases": []
            }

    if not all_entity_targets:
        # Fallback if no entities extracted
        stem_name = Path(source_filename).stem.replace("_", " ").title()
        all_entity_targets[stem_name] = {
            "entity_name": stem_name,
            "entity_type": "DOCUMENT",
            "description": f"Document entity for {source_filename}",
            "aliases": []
        }

    # Process each entity
    for entity_name, ent_info in all_entity_targets.items():
        safe_filename = _sanitize_filename(entity_name) + ".md"
        page_path = target_dir / safe_filename
        
        entity_rels = rel_map.get(entity_name, [])
        if not entity_rels:
            doc_stem = Path(source_filename).stem.replace("_", " ").title()
            hub_target = doc_stem if doc_stem != entity_name else (list(all_entity_targets.keys())[0] if list(all_entity_targets.keys())[0] != entity_name else "")
            if hub_target:
                entity_rels = [{"source": entity_name, "relation": "MENTIONED_IN", "target": hub_target}]

        related_entity_names = set()
        for r in entity_rels:
            if r["source"] == entity_name and r["target"]:
                related_entity_names.add(r["target"])
            elif r["target"] == entity_name and r["source"]:
                related_entity_names.add(r["source"])

        # Helper for flexible entity matching so facts are never dropped due to name variations
        def _is_entity_match(target_name: str, aliases: List[str], text: str) -> bool:
            if not text:
                return False
            t_low = text.lower()
            if target_name.lower() in t_low:
                return True
            for a in aliases:
                if a and a.lower() in t_low:
                    return True
            # Check token overlap for names (words with len >= 4)
            name_tokens = [w.lower() for w in re.split(r"\W+", target_name) if len(w) >= 4]
            if any(tok in t_low for tok in name_tokens):
                return True
            # Fallback: if document has 1-2 primary entities, assign all unassigned facts to primary
            if len(all_entity_targets) <= 2:
                return True
            return False

        # Gather relevant facts, claims, timelines
        ent_facts = [
            f for f in facts 
            if _is_entity_match(entity_name, ent_info["aliases"], f.get("subject", "")) or _is_entity_match(entity_name, ent_info["aliases"], f.get("statement", ""))
        ]
        ent_claims = [
            c for c in claims 
            if _is_entity_match(entity_name, ent_info["aliases"], c.get("claim", "")) or _is_entity_match(entity_name, ent_info["aliases"], c.get("evidence", ""))
        ]
        ent_timelines = [
            t for t in timelines 
            if _is_entity_match(entity_name, ent_info["aliases"], t.get("event_title", "")) or _is_entity_match(entity_name, ent_info["aliases"], t.get("description", ""))
        ]
        ent_contradictions = [
            c for c in contradictions 
            if _is_entity_match(entity_name, ent_info["aliases"], c.get("subject", ""))
        ]

        if page_path.exists():
            # Update existing page
            existing_content = page_path.read_text(encoding="utf-8")
            updated_content = _merge_into_existing_page(
                existing_content=existing_content,
                entity_info=ent_info,
                source_filename=source_filename,
                today_str=today_str,
                new_facts=ent_facts,
                new_claims=ent_claims,
                new_relationships=entity_rels,
                new_related=related_entity_names,
                new_timelines=ent_timelines,
                new_contradictions=ent_contradictions
            )
            page_path.write_text(updated_content, encoding="utf-8")
            pages_updated.append(entity_name)

            page_records.append({
                "entity_name": entity_name,
                "filename": safe_filename,
                "entity_type": ent_info["entity_type"],
                "related_entities": list(related_entity_names),
                "relationships": entity_rels,
                "content": updated_content,
                "path": str(page_path.resolve()),
                "status": "updated"
            })

        else:
            # Create new page
            new_content = _create_new_page_content(
                entity_info=ent_info,
                source_filename=source_filename,
                today_str=today_str,
                facts=ent_facts,
                claims=ent_claims,
                relationships=entity_rels,
                related=related_entity_names,
                timelines=ent_timelines,
                contradictions=ent_contradictions
            )
            page_path.write_text(new_content, encoding="utf-8")
            pages_created.append(entity_name)

            page_records.append({
                "entity_name": entity_name,
                "filename": safe_filename,
                "entity_type": ent_info["entity_type"],
                "related_entities": list(related_entity_names),
                "relationships": entity_rels,
                "content": new_content,
                "path": str(page_path.resolve()),
                "status": "created"
            })

    # Update backlinks across all entity pages in wiki_dir
    _update_backlinks_in_wiki(target_dir, [p["entity_name"] for p in page_records])

    return {
        "pages_created": pages_created,
        "pages_updated": pages_updated,
        "total_affected": len(pages_created) + len(pages_updated),
        "page_records": page_records,
        "contradictions_flagged": contradictions
    }


def _create_new_page_content(
    entity_info: Dict[str, Any],
    source_filename: str,
    today_str: str,
    facts: List[Dict[str, Any]],
    claims: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]],
    related: Set[str],
    timelines: List[Dict[str, Any]],
    contradictions: List[Dict[str, Any]]
) -> str:
    """Format markdown content for a new Wiki page adhering strictly to source knowledge boundaries."""
    entity_name = entity_info["entity_name"]
    entity_type = entity_info["entity_type"]
    overview = entity_info["description"] or "Mentioned in uploaded source document without additional background details."

    fact_items = []
    for f in facts:
        stmt = f.get('statement', '')
        prov = f.get('provenance')
        prov_str = f" (Provenance: {prov})" if prov else ""
        fact_items.append(f"- {stmt}{prov_str}")
    
    facts_md = "\n".join(fact_items) if fact_items else "- Mentioned in uploaded source document without additional factual statements."
    
    claims_md = ""
    if claims:
        claim_lines = [f"- **Claim**: {c.get('claim')}  \n  *Evidence*: {c.get('evidence', 'None')}" for c in claims]
        claims_md = "\n\n### Verified Claims & Evidence\n" + "\n".join(claim_lines)

    rel_lines = []
    for r in relationships:
        rel_lines.append(f"- [[{r['source']}]] --[`{r['relation']}`]--> [[{r['target']}]]")
    rel_md = "\n".join(rel_lines) if rel_lines else "- No explicit relationships defined in source text."

    related_md = ", ".join(f"[[{r}]]" for r in sorted(related)) if related else "None"

    timeline_md = ""
    if timelines:
        timeline_lines = [f"- **{t.get('date_or_period', 'Event')}**: {t.get('event_title')} - {t.get('description')}" for t in timelines]
        timeline_md = "\n\n## Timeline & Events\n" + "\n".join(timeline_lines)

    contradiction_md = ""
    if contradictions:
        c_lines = [f"- ⚠️ **Subject**: {c.get('subject')}\n  - Statement A: {c.get('conflicting_statement_a')}\n  - Statement B: {c.get('conflicting_statement_b')}\n  - Note: {c.get('explanation')}" for c in contradictions]
        contradiction_md = "\n\n## Contradictions / Conflicting Claims\n" + "\n".join(c_lines)

    content = f"""# {entity_name}

**Entity Type**: `{entity_type}`  
**Last Updated**: `{today_str}`

## Information from Uploaded Sources

### Document Provenance
- Mentioned in: [{source_filename}](file://{source_filename})

### Overview
{overview}

### Known Facts & Data
{facts_md}{claims_md}

## Related Entities
{related_md}

## Knowledge Graph Relationships
{rel_md}{timeline_md}{contradiction_md}

## Backlinks
- No backlinks recorded yet.

## Document Sources
- [{source_filename}](file://{source_filename})
"""
    return content


def _merge_into_existing_page(
    existing_content: str,
    entity_info: Dict[str, Any],
    source_filename: str,
    today_str: str,
    new_facts: List[Dict[str, Any]],
    new_claims: List[Dict[str, Any]],
    new_relationships: List[Dict[str, Any]],
    new_related: Set[str],
    new_timelines: List[Dict[str, Any]],
    new_contradictions: List[Dict[str, Any]]
) -> str:
    """Merge new knowledge incrementally into an existing Wiki page without overwriting."""
    lines = existing_content.split("\n")

    # Update Last Updated date
    for i, line in enumerate(lines[:10]):
        if line.startswith("**Last Updated**"):
            lines[i] = f"**Last Updated**: `{today_str}`"

    content = "\n".join(lines)

    # Append new facts if not already present
    if new_facts:
        fact_additions = []
        for f in new_facts:
            stmt = f.get("statement", "").strip()
            if stmt and stmt not in content:
                fact_additions.append(f"- {stmt} (Confidence: {f.get('confidence', 0.95)})")
        
        if fact_additions and "## Key Facts" in content:
            content = content.replace("## Key Facts\n- No facts recorded yet.", "## Key Facts")
            content = content.replace("## Key Facts", "## Key Facts\n" + "\n".join(fact_additions))

    # Append new relationships
    if new_relationships:
        rel_additions = []
        for r in new_relationships:
            r_str = f"- [[{r['source']}]] --[`{r['relation']}`]--> [[{r['target']}]]"
            if r_str not in content:
                rel_additions.append(r_str)
        if rel_additions and "## Knowledge Graph Relationships" in content:
            content = content.replace("## Knowledge Graph Relationships\n- No explicit relationships defined.", "## Knowledge Graph Relationships")
            content = content.replace("## Knowledge Graph Relationships", "## Knowledge Graph Relationships\n" + "\n".join(rel_additions))

    # Append new source document citation if not already present
    doc_link = f"- [{source_filename}](file://{source_filename})"
    if doc_link not in content:
        if "## Document Sources" in content:
            content = content.replace("## Document Sources", f"## Document Sources\n{doc_link}")
        else:
            content += f"\n\n## Document Sources\n{doc_link}\n"

    # Flag contradictions if present
    if new_contradictions:
        c_lines = [f"- ⚠️ **Subject**: {c.get('subject')}\n  - Statement A: {c.get('conflicting_statement_a')}\n  - Statement B: {c.get('conflicting_statement_b')}\n  - Note: {c.get('explanation')}" for c in new_contradictions]
        if "## Contradictions / Conflicting Claims" in content:
            content = content.replace("## Contradictions / Conflicting Claims", "## Contradictions / Conflicting Claims\n" + "\n".join(c_lines))
        else:
            content += "\n\n## Contradictions / Conflicting Claims\n" + "\n".join(c_lines)

    return content


def _update_backlinks_in_wiki(wiki_dir: Path, target_entity_names: List[str]):
    """Update backlinks section across all markdown pages in the wiki directory."""
    all_md_files = list(wiki_dir.glob("*.md"))
    all_pages_map = {}

    for f in all_md_files:
        if f.name in ["Index.md", "log.md"]:
            continue
        try:
            txt = f.read_text(encoding="utf-8")
            entity_title = f.stem.replace("_", " ")
            all_pages_map[entity_title] = (f, txt)
        except Exception:
            continue

    # Find backlinks for each page
    for target_name, (target_path, target_txt) in all_pages_map.items():
        linking_pages = []
        for other_name, (other_path, other_txt) in all_pages_map.items():
            if other_name != target_name and f"[[{target_name}]]" in other_txt:
                linking_pages.append(other_name)

        if "## Backlinks" in target_txt:
            if linking_pages:
                backlinks_md = "## Backlinks\n" + "\n".join(f"- [[{p}]]" for p in sorted(linking_pages))
            else:
                backlinks_md = "## Backlinks\n- No backlinks recorded yet."

            new_target_txt = re.sub(
                r"## Backlinks\n.*?(?=\n## |\Z)",
                backlinks_md,
                target_txt,
                flags=re.DOTALL
            )

            if new_target_txt != target_txt:
                target_path.write_text(new_target_txt, encoding="utf-8")


def _sanitize_filename(name: str) -> str:
    """Sanitize string for safe cross-platform file names."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    return clean.strip().replace(" ", "_")
