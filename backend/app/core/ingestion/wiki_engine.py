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

from ..graph_db import save_wiki_page, get_wiki_page_by_title, get_user_wiki_pages


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
    user_id = target_dir.name if "users" in target_dir.parts else "default_user"


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
    people = knowledge_json.get("people", [])
    authors = knowledge_json.get("authors", [])

    pages_created = []
    pages_updated = []
    page_records = []

    # Map relationships and entity targets using canonical lookup
    all_entity_targets: Dict[str, Dict[str, Any]] = {}
    canonical_map: Dict[str, str] = {}

    def _get_or_create_canonical_name(name: str) -> str:
        clean_name = name.strip()
        if not clean_name:
            return ""
        
        # Remove file extension if present (e.g. .pdf, .docx)
        if "." in clean_name and len(clean_name.rsplit(".", 1)[-1]) <= 4:
            clean_name = clean_name.rsplit(".", 1)[0].strip()

        norm_key = re.sub(r"[\s_\-]+", " ", clean_name.lower())

        # Check direct normalized key match
        for existing_low, canonical in list(canonical_map.items()):
            ex_norm = re.sub(r"[\s_\-]+", " ", existing_low)
            if norm_key == ex_norm:
                if clean_name != canonical and clean_name[0].isupper() and canonical[0].islower():
                    canonical_map[existing_low] = clean_name
                    canonical_map[norm_key] = clean_name
                    return clean_name
                return canonical

        # Dynamic prefix matching with normalized delimiters (Zero hardcoded suffix lists)
        for existing_low, canonical in list(canonical_map.items()):
            ex_norm = re.sub(r"[\s_\-]+", " ", existing_low)
            if norm_key.startswith(ex_norm + " "):
                canonical_map[norm_key] = canonical
                return canonical
            elif ex_norm.startswith(norm_key + " "):
                canonical_map[existing_low] = clean_name
                canonical_map[norm_key] = clean_name
                return clean_name

        canonical_map[norm_key] = clean_name
        return clean_name

    # 1. Group primary entity targets first so Title-Case canonical names are registered
    for ent in entities:
        name = ent.get("name", "").strip()
        c_name = _get_or_create_canonical_name(name)
        if c_name:
            if c_name not in all_entity_targets:
                all_entity_targets[c_name] = {
                    "entity_name": c_name,
                    "entity_type": ent.get("type", "CONCEPT").strip().upper(),
                    "description": ent.get("description", "").strip(),
                    "aliases": ent.get("aliases", [])
                }
            else:
                curr_desc = all_entity_targets[c_name].get("description", "")
                new_desc = ent.get("description", "").strip()
                if len(new_desc) > len(curr_desc):
                    all_entity_targets[c_name]["description"] = new_desc
                for alias in ent.get("aliases", []):
                    if alias and alias not in all_entity_targets[c_name]["aliases"]:
                        all_entity_targets[c_name]["aliases"].append(alias)

    # 2. Map relationships using canonical names
    rel_map: Dict[str, List[Dict[str, str]]] = {}
    for rel in relationships:
        src_raw = rel.get("source", "").strip()
        tgt_raw = rel.get("target", "").strip()
        src = _get_or_create_canonical_name(src_raw) if src_raw else ""
        tgt = _get_or_create_canonical_name(tgt_raw) if tgt_raw else ""
        rel_type = rel.get("relation", "RELATED_TO").strip()
        if src:
            rel_map.setdefault(src, []).append({"source": src, "relation": rel_type, "target": tgt})
        if tgt and tgt != src:
            rel_map.setdefault(tgt, []).append({"source": src, "relation": rel_type, "target": tgt})

    # 3. Ensure concepts without entity records are included
    for conc in concepts:
        c_raw = conc.get("name", "").strip() if isinstance(conc, dict) else str(conc).strip()
        c_name = _get_or_create_canonical_name(c_raw)
        if c_name and c_name not in all_entity_targets:
            all_entity_targets[c_name] = {
                "entity_name": c_name,
                "entity_type": "CONCEPT",
                "description": conc.get("definition", "").strip() if isinstance(conc, dict) else f"Extracted concept entity from {source_filename}.",
                "aliases": []
            }

    # 4. Ensure organisations and locations are registered
    orgs = knowledge_json.get("organisations", [])
    for org in orgs:
        o_raw = org.strip() if isinstance(org, str) else ""
        o_name = _get_or_create_canonical_name(o_raw)
        if o_name and o_name not in all_entity_targets:
            all_entity_targets[o_name] = {
                "entity_name": o_name,
                "entity_type": "ORGANIZATION",
                "description": f"Extracted organization entity from source document {source_filename}.",
                "aliases": []
            }

    locs = knowledge_json.get("locations", [])
    for loc in locs:
        l_raw = loc.strip() if isinstance(loc, str) else ""
        l_name = _get_or_create_canonical_name(l_raw)
        if l_name and l_name not in all_entity_targets:
            all_entity_targets[l_name] = {
                "entity_name": l_name,
                "entity_type": "LOCATION",
                "description": f"Extracted location entity from source document {source_filename}.",
                "aliases": []
            }

    # 5. Ensure document people and authors are registered as PERSON entities
    people = knowledge_json.get("people", []) + knowledge_json.get("authors", [])
    for p in people:
        p_raw = p.strip() if isinstance(p, str) else ""
        p_name = _get_or_create_canonical_name(p_raw)
        if p_name and p_name not in all_entity_targets:
            all_entity_targets[p_name] = {
                "entity_name": p_name,
                "entity_type": "PERSON",
                "description": f"Extracted person entity from source document {source_filename}.",
                "aliases": []
            }

    # 6. Ensure projects, products, and software systems are registered as PRODUCT/SYSTEM entities
    projects = knowledge_json.get("projects", []) + knowledge_json.get("products", [])
    for proj in projects:
        proj_raw = proj.strip() if isinstance(proj, str) else (proj.get("name") if isinstance(proj, dict) else "")
        proj_name = _get_or_create_canonical_name(proj_raw)
        if proj_name and proj_name not in all_entity_targets:
            all_entity_targets[proj_name] = {
                "entity_name": proj_name,
                "entity_type": "PRODUCT",
                "description": f"Extracted project/product/system entity from source document {source_filename}.",
                "aliases": []
            }

    # 7. Ensure any relationship source/target entities are registered
    for rel in relationships:
        for term in [rel.get("source", ""), rel.get("target", "")]:
            t_raw = term.strip() if isinstance(term, str) else ""
            t_name = _get_or_create_canonical_name(t_raw)
            if t_name and t_name not in all_entity_targets:
                all_entity_targets[t_name] = {
                    "entity_name": t_name,
                    "entity_type": "CONCEPT",
                    "description": f"Extracted connected entity from source document {source_filename}.",
                    "aliases": []
                }


    # Process each entity
    for entity_name, ent_info in all_entity_targets.items():
        safe_filename = _sanitize_filename(entity_name) + ".md"
        page_path = target_dir / safe_filename

        
        # Determine primary subject hub for fallback relationships (prefer PERSON entity)
        primary_hub_entity = None
        for name_key, info in all_entity_targets.items():
            if info.get("entity_type") == "PERSON":
                primary_hub_entity = name_key
                break
        if not primary_hub_entity:
            primary_hub_entity = list(all_entity_targets.keys())[0] if all_entity_targets else ""

        entity_rels = rel_map.get(entity_name, [])
        if not entity_rels and primary_hub_entity and primary_hub_entity != entity_name:
            entity_rels = [{"source": entity_name, "relation": "MENTIONED_IN", "target": primary_hub_entity}]

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

        existing_db_rec = get_wiki_page_by_title(user_id, entity_name)
        if existing_db_rec or (page_path and page_path.exists()):
            # Update existing page content
            existing_content = existing_db_rec["content"] if existing_db_rec and existing_db_rec.get("content") else (page_path.read_text(encoding="utf-8") if page_path.exists() else "")
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
            pages_updated.append(entity_name)

            save_wiki_page(
                user_id=user_id,
                title=entity_name,
                summary=ent_info.get("description", ""),
                content=updated_content,
                category=ent_info.get("entity_type", "General"),
                file_name=safe_filename,
                linked_titles=list(related_entity_names)
            )

            page_records.append({
                "entity_name": entity_name,
                "title": entity_name,
                "filename": safe_filename,
                "file_name": safe_filename,
                "entity_type": ent_info["entity_type"],
                "category": ent_info["entity_type"],
                "summary": ent_info.get("description", ""),
                "related_entities": list(related_entity_names),
                "links": list(related_entity_names),
                "relationships": entity_rels,
                "content": updated_content,
                "path": safe_filename,
                "status": "updated"
            })

        else:
            # Create new page & save directly to Neo4j Graph DB
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
            pages_created.append(entity_name)

            save_wiki_page(
                user_id=user_id,
                title=entity_name,
                summary=ent_info.get("description", ""),
                content=new_content,
                category=ent_info.get("entity_type", "General"),
                file_name=safe_filename,
                linked_titles=list(related_entity_names)
            )

            page_records.append({
                "entity_name": entity_name,

                "title": entity_name,
                "filename": safe_filename,
                "file_name": safe_filename,
                "entity_type": ent_info["entity_type"],
                "category": ent_info["entity_type"],
                "summary": ent_info.get("description", ""),
                "related_entities": list(related_entity_names),
                "links": list(related_entity_names),
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
    desc_raw = (entity_info.get("description") or "").strip()
    if not desc_raw or "without additional background details" in desc_raw or "Auto-referenced" in desc_raw:
        if relationships:
            rel_summary = ", ".join([f"{r['relation'].lower().replace('_', ' ')} [[{r['target']}]]" for r in relationships[:3] if r.get('target')])
            if rel_summary:
                overview = f"{entity_name} is an entity extracted from [{source_filename}](file://{source_filename}) associated with {rel_summary}."
            else:
                overview = f"{entity_name} is a key concept identified in [{source_filename}](file://{source_filename})."
        else:
            overview = f"{entity_name} is a key entity identified in [{source_filename}](file://{source_filename})."
    else:
        overview = desc_raw


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

    # Update overview if new detailed description is available
    new_desc = (entity_info.get("description") or "").strip()
    if new_desc and "without additional background details" not in new_desc and "Auto-referenced" not in new_desc:
        if re.search(r"#*\s*Overview", content, re.IGNORECASE):
            content = re.sub(r"#*\s*Overview\n.*?(?=\n#+ |\n\n## |\Z)", f"### Overview\n{new_desc}\n\n", content, flags=re.DOTALL | re.IGNORECASE)
        elif "Auto-referenced entity concept" in content or "without additional background details" in content:
            content = re.sub(r"(Auto-referenced entity concept.*?\n|Mentioned in uploaded source document.*?\n)", f"{new_desc}\n", content)
        elif "## Information from Uploaded Sources" in content:
            content = content.replace("## Information from Uploaded Sources", f"## Information from Uploaded Sources\n\n### Overview\n{new_desc}")
        else:
            content += f"\n\n### Overview\n{new_desc}\n"


    # Append new facts if not already present
    if new_facts:
        fact_additions = []
        for f in new_facts:
            stmt = f.get("statement", "").strip()
            if stmt and stmt not in content:
                fact_additions.append(f"- {stmt}")
        
        if fact_additions:
            if "### Known Facts & Data" in content:
                content = content.replace("### Known Facts & Data\n- Mentioned in uploaded source document without additional factual statements.", "### Known Facts & Data")
                content = content.replace("### Known Facts & Data", "### Known Facts & Data\n" + "\n".join(fact_additions))
            elif "## Key Facts" in content:
                content = content.replace("## Key Facts\n- No facts recorded yet.", "## Key Facts")
                content = content.replace("## Key Facts", "## Key Facts\n" + "\n".join(fact_additions))
            else:
                content += "\n\n### Known Facts & Data\n" + "\n".join(fact_additions)

    # Append new relationships
    if new_relationships:
        rel_additions = []
        for r in new_relationships:
            r_str = f"- [[{r['source']}]] --[`{r['relation']}`]--> [[{r['target']}]]"
            if r_str not in content:
                rel_additions.append(r_str)
        if rel_additions:
            if "## Knowledge Graph Relationships" in content:
                content = content.replace("## Knowledge Graph Relationships\n- No explicit relationships defined in source text.", "## Knowledge Graph Relationships")
                content = content.replace("## Knowledge Graph Relationships", "## Knowledge Graph Relationships\n" + "\n".join(rel_additions))
            else:
                content += "\n\n## Knowledge Graph Relationships\n" + "\n".join(rel_additions)

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
    """Update backlinks section across all entity database records."""
    from ..graph_db import get_user_wiki_pages, save_wiki_page

    user_id = wiki_dir.name if "users" in wiki_dir.parts else "default_user"
    db_pages = get_user_wiki_pages(user_id)
    if not db_pages:
        # Filesystem fallback if graph db has no pages yet
        md_files = list(wiki_dir.glob("*.md"))
        db_pages = []
        for f in md_files:
            if f.name not in ["Index.md", "README.md"]:
                entity = f.stem.replace("_", " ")
                content = f.read_text(encoding="utf-8")
                db_pages.append({
                    "title": entity,
                    "content": content,
                    "category": "General",
                    "file_name": f.name,
                    "links": []
                })

    all_pages_map = {p["title"]: p for p in db_pages if p.get("title")}

    # Find backlinks for each page
    for target_name, target_rec in all_pages_map.items():
        target_txt = target_rec.get("content", "")
        linking_pages = []
        for other_name, other_rec in all_pages_map.items():
            if other_name != target_name and f"[[{target_name}]]" in other_rec.get("content", ""):
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
                safe_fn = _sanitize_filename(target_name) + ".md"
                save_wiki_page(
                    user_id=user_id,
                    title=target_name,
                    summary=target_rec.get("summary", ""),
                    content=new_target_txt,
                    category=target_rec.get("category", "General"),
                    file_name=safe_fn,
                    linked_titles=target_rec.get("links", [])
                )





def _sanitize_filename(name: str) -> str:
    """Sanitize string for safe cross-platform file names."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    return clean.strip().replace(" ", "_")
