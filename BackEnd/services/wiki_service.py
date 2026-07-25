import os
import re
import json
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from fastapi import HTTPException, status

from BackEnd.schemas import (
    WikiPageSummary,
    WikiPageResponse,
    WikiIndexResponse,
    WikiGenerationResponse,
    KnowledgeExtractionResponse
)
from BackEnd.services.knowledge_service import knowledge_service
from BackEnd.services.metadata_service import metadata_service

BACKEND_DIR = Path(__file__).resolve().parent.parent

class WikiService:
    def __init__(self, wiki_dir: str = "./BackEnd/storage/wiki"):
        if isinstance(wiki_dir, str) and wiki_dir.startswith("./"):
            clean_rel = wiki_dir[2:]
            if clean_rel.startswith("BackEnd/"):
                self.wiki_dir = (BACKEND_DIR.parent / clean_rel).resolve()
            else:
                self.wiki_dir = (BACKEND_DIR / "storage" / clean_rel.replace("storage/", "")).resolve()
        else:
            self.wiki_dir = Path(wiki_dir).resolve()
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
        self.index_json_path = self.wiki_dir / "index.json"
        self.index_md_path = self.wiki_dir / "Index.md"

    def clean_entity_name(self, name: str) -> str:
        """Strip page dividers, headers, line breaks, and excess whitespace from entity name"""
        if not name:
            return ""
        clean = re.sub(r'---\s*Page\s*\d+\s*---', '', name, flags=re.IGNORECASE)
        clean = re.sub(r'[\r\n\t]+', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def sanitize_filename(self, name: str) -> str:
        """Sanitize entity name into a safe Markdown filename (e.g. 'Elon Musk' -> 'Elon_Musk.md')"""
        clean_name = self.clean_entity_name(name)
        clean_name = re.sub(r'[\\/*?:"<>|\r\n\t]', '_', clean_name)
        clean_name = clean_name.replace(" ", "_")
        return f"{clean_name}.md" if clean_name else "Entity.md"

    def format_wiki_link(self, target_entity: str) -> str:
        """Formats an internal markdown link using both [[Wiki Link]] and relative link [Target](Target.md)"""
        filename = self.sanitize_filename(target_entity)
        encoded_filename = urllib.parse.quote(filename)
        return f"[[{target_entity}]] ([{target_entity}]({encoded_filename}))"

    def generate_wiki_for_document(self, file_id: str) -> WikiGenerationResponse:
        """
        Main Orchestrator: Fetches Knowledge extraction artifact for file_id,
        creates/merges a markdown page for every entity, adds internal cross-links,
        rebuilds Index.md / index.json, and updates metadata status to 'wiki_generated'.
        """
        knowledge = knowledge_service.get_knowledge_document(file_id)
        if not knowledge:
            knowledge = knowledge_service.extract_knowledge_for_document(file_id)

        if not knowledge.entities and not knowledge.summary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Knowledge extraction output for document '{file_id}' is empty."
            )

        all_known_entities: Set[str] = {e.name for e in knowledge.entities}
        for rel in knowledge.relationships:
            if rel.source_entity:
                all_known_entities.add(rel.source_entity)
            if rel.target_entity:
                all_known_entities.add(rel.target_entity)

        generated_summaries: List[WikiPageSummary] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # Build wiki page per entity
        for entity in knowledge.entities:
            entity_name = self.clean_entity_name(entity.name)
            if not entity_name or len(entity_name) < 2:
                continue
            entity_type = entity.type
            description = entity.description or "Extracted entity from domain document."
            filename = self.sanitize_filename(entity_name)
            filepath = self.wiki_dir / filename

            matching_defs = [d for d in knowledge.definitions if d.term.lower() == entity_name.lower()]
            matching_facts = [f for f in knowledge.facts if entity_name.lower() in f.fact.lower()]
            matching_rels = [
                r for r in knowledge.relationships 
                if r.source_entity.lower() == entity_name.lower() or r.target_entity.lower() == entity_name.lower()
            ]

            links_to: Set[str] = set()
            rel_lines: List[str] = []

            for r in matching_rels:
                if r.source_entity.lower() == entity_name.lower():
                    other_entity = r.target_entity
                    direction_str = f"**{r.relation}** $\\rightarrow$ {self.format_wiki_link(other_entity)}"
                else:
                    other_entity = r.source_entity
                    direction_str = f"{self.format_wiki_link(other_entity)} $\\rightarrow$ **{r.relation}**"

                links_to.add(other_entity)
                rel_desc = f": {r.description}" if r.description else ""
                rel_lines.append(f"- {direction_str}{rel_desc}")

            md_lines: List[str] = [
                f"# {entity_name}\n",
                f"**Entity Type**: `{entity_type}`  ",
                f"**Last Updated**: `{now_iso[:10]}`\n",
                "## Overview",
                description,
                ""
            ]

            if matching_defs:
                md_lines.append("## Definitions")
                for d in matching_defs:
                    md_lines.append(f"- **{d.term}**: {d.definition}")
                md_lines.append("")

            if matching_facts:
                md_lines.append("## Key Facts")
                for f in matching_facts:
                    md_lines.append(f"- {f.fact} *(Confidence: {f.confidence})*")
                md_lines.append("")

            if rel_lines:
                md_lines.append("## Connected Entities & Relationships")
                md_lines.extend(rel_lines)
                md_lines.append("")

            md_lines.append("## Document Sources")
            md_lines.append(f"- [{knowledge.original_filename}](file:///{knowledge.file_id}) (File ID: `{knowledge.file_id}`)")
            md_lines.append("")

            page_content = "\n".join(md_lines)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(page_content)

            # Sync Wiki Page Record to Database
            try:
                from BackEnd.services.db_service import db_service
                db_service.save_wiki_page(
                    entity_name=entity_name,
                    filename=filename,
                    entity_type=entity_type,
                    filepath=str(filepath),
                    content=page_content,
                    links=list(links_to),
                    updated_at=now_iso
                )
            except Exception:
                pass

            summary_item = WikiPageSummary(
                entity_name=entity_name,
                filename=filename,
                entity_type=entity_type,
                link_count=len(links_to),
                updated_at=now_iso
            )
            generated_summaries.append(summary_item)

        self.rebuild_index()

        metadata = metadata_service.get_metadata_by_id(file_id)
        if metadata:
            metadata.status = "wiki_generated"
            metadata_service.save_metadata(metadata)

        return WikiGenerationResponse(
            file_id=file_id,
            total_pages_generated=len(generated_summaries),
            pages_generated=generated_summaries,
            status="wiki_generated",
            message=f"Successfully generated {len(generated_summaries)} wiki markdown pages."
        )

    def rebuild_index(self) -> WikiIndexResponse:
        """Scans the ./wiki/ directory for .md files, updates index.json, and rewrites Index.md"""
        wiki_files = [p for p in self.wiki_dir.glob("*.md") if p.name not in ("Index.md", "README.md")]
        pages: List[WikiPageSummary] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        index_md_lines = [
            "# WikiMind Knowledge Base Index\n",
            f"**Total Topic Pages**: `{len(wiki_files)}` | **Last Rebuilt**: `{now_iso}`\n",
            "---",
            "\n## Available Topics\n"
        ]

        for filepath in sorted(wiki_files, key=lambda p: p.name.lower()):
            entity_name = filepath.stem.replace("_", " ")
            entity_type = "CONCEPT"
            link_count = 0
            try:
                content = filepath.read_text(encoding="utf-8")
                type_match = re.search(r'\*\*Entity Type\*\*:\s*`([^`]+)`', content)
                if type_match:
                    entity_type = type_match.group(1)
                link_matches = re.findall(r'\[\[(.*?)\]\]', content)
                link_count = len(set(link_matches))
            except Exception:
                pass

            encoded_filename = urllib.parse.quote(filepath.name)
            index_md_lines.append(f"- [{entity_name}]({encoded_filename}) (`{entity_type}`) — *{link_count} connections*")

            pages.append(WikiPageSummary(
                entity_name=entity_name,
                filename=filepath.name,
                entity_type=entity_type,
                link_count=link_count,
                updated_at=now_iso
            ))

        with open(self.index_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(index_md_lines))

        index_data = {
            "total_pages": len(pages),
            "rebuilt_at": now_iso,
            "pages": [p.model_dump() for p in pages]
        }
        with open(self.index_json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(index_data, indent=2))

        return WikiIndexResponse(
            total_pages=len(pages),
            pages=pages
        )

    def get_wiki_index(self) -> WikiIndexResponse:
        """Returns the current wiki catalog index"""
        if not self.index_json_path.exists():
            return self.rebuild_index()
        try:
            with open(self.index_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return WikiIndexResponse(
                    total_pages=data.get("total_pages", 0),
                    pages=[WikiPageSummary(**p) for p in data.get("pages", [])]
                )
        except Exception:
            return self.rebuild_index()

    def get_wiki_page(self, entity_name: str) -> Optional[WikiPageResponse]:
        """Retrieves a specific Wiki page by entity name or filename"""
        filename = self.sanitize_filename(entity_name)
        filepath = self.wiki_dir / filename

        if not filepath.exists():
            alt_path = self.wiki_dir / entity_name
            if alt_path.exists():
                filepath = alt_path
            else:
                return None

        content = filepath.read_text(encoding="utf-8")
        type_match = re.search(r'\*\*Entity Type\*\*:\s*`([^`]+)`', content)
        entity_type = type_match.group(1) if type_match else "CONCEPT"
        
        links = list(set(re.findall(r'\[\[(.*?)\]\]', content)))

        return WikiPageResponse(
            entity_name=filepath.stem.replace("_", " "),
            filename=filepath.name,
            entity_type=entity_type,
            content=content,
            links_to=links,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="generated"
        )

# Default singleton instance
wiki_service = WikiService()
