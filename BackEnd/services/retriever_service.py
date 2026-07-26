import re
from pathlib import Path
from typing import List, Dict, Set, Any, Optional
from fastapi import HTTPException, status

from BackEnd.schemas import (
    RetrievedPageDetail,
    RetrievalRequest,
    RetrievalContextResponse
)
from BackEnd.services.vector_service import vector_service
from BackEnd.services.wiki_service import wiki_service
from BackEnd.services.db_service import db_service

BACKEND_DIR = Path(__file__).resolve().parent.parent

class IntelligentRetriever:
    def __init__(self):
        pass

    def retrieve_multi_hop_context(
        self,
        question: str,
        top_k: int = 3,
        max_chars: int = 4000
    ) -> RetrievalContextResponse:
        """
        Executes multi-hop retrieval:
        1. Hop 1: Vector similarity search for primary seed pages.
        2. Hop 2: Graph expansion over internal wiki links ([[Target Entity]]) and DB relationships.
        3. Assembly: Deduplicates, formats markdown, and enforces max_chars budgeting.
        """
        q_str = question.strip()
        if not q_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retrieval question string cannot be empty."
            )

        # --- Hop 1: Primary Vector Semantic Search ---
        search_res = vector_service.semantic_search(query=q_str, top_k=top_k)
        primary_matches = search_res.results

        retrieved_pages: List[RetrievedPageDetail] = []
        seen_entities: Set[str] = set()

        # Hop 1 Processing
        for match in primary_matches:
            name = match.entity_name
            seen_entities.add(name.lower())

            # Retrieve full page content from wiki service
            page = wiki_service.get_wiki_page(name)
            page_content = page.content if page else match.snippet

            retrieved_pages.append(RetrievedPageDetail(
                entity_name=name,
                filename=match.filename,
                hop_level=1,
                relevance_score=match.similarity_score,
                connection_reason="Direct Vector Match (Hop 1)",
                snippet=match.snippet,
                content=page_content
            ))

        # --- Hop 2: Graph & Wiki Link Expansion ---
        hop2_candidates: List[RetrievedPageDetail] = []
        
        for primary_page in retrieved_pages:
            content = primary_page.content
            # Extract internal links [[Target Entity]]
            linked_targets = re.findall(r'\[\[(.*?)\]\]', content)

            for target in linked_targets:
                clean_target = target.strip()
                if clean_target.lower() in seen_entities or not clean_target:
                    continue

                seen_entities.add(clean_target.lower())
                target_page = wiki_service.get_wiki_page(clean_target)

                if target_page:
                    snippet = " ".join([
                        l.strip() for l in target_page.content.splitlines() 
                        if l.strip() and not l.startswith("#")
                    ][:2])[:200]

                    hop2_candidates.append(RetrievedPageDetail(
                        entity_name=target_page.entity_name,
                        filename=target_page.filename,
                        hop_level=2,
                        relevance_score=round(primary_page.relevance_score * 0.85, 4),
                        connection_reason=f"Connected via [[{clean_target}]] on {primary_page.entity_name} (Hop 2)",
                        snippet=snippet,
                        content=target_page.content
                    ))

        # Combine Hop 1 and Hop 2
        all_pages = retrieved_pages + hop2_candidates

        # --- Context Assembly & Character Budgeting ---
        context_blocks: List[str] = [
            "# RETRIEVED KNOWLEDGE CONTEXT FOR LLM QA",
            f"**Question**: `{q_str}`\n"
        ]

        current_char_count = sum(len(b) for b in context_blocks)
        final_pages: List[RetrievedPageDetail] = []
        primary_count = len(retrieved_pages)
        related_count = 0

        for p in all_pages:
            # Format block for page
            block = (
                f"### Page: {p.entity_name} (Hop {p.hop_level} | Score: {p.relevance_score})\n"
                f"**Connection**: `{p.connection_reason}`\n\n"
                f"{p.content}\n\n"
                f"---\n"
            )

            if current_char_count + len(block) > max_chars:
                # If adding full page exceeds limit, try adding snippet if possible
                snippet_block = (
                    f"### Page: {p.entity_name} (Hop {p.hop_level} | Score: {p.relevance_score} - Snippet)\n"
                    f"**Connection**: `{p.connection_reason}`\n\n"
                    f"{p.snippet}\n\n"
                    f"---\n"
                )
                if current_char_count + len(snippet_block) <= max_chars:
                    context_blocks.append(snippet_block)
                    current_char_count += len(snippet_block)
                    final_pages.append(p)
                    if p.hop_level == 2:
                        related_count += 1
                break  # Reached max budget
            else:
                context_blocks.append(block)
                current_char_count += len(block)
                final_pages.append(p)
                if p.hop_level == 2:
                    related_count += 1

        assembled_text = "\n".join(context_blocks)

        return RetrievalContextResponse(
            question=q_str,
            primary_pages_count=primary_count,
            related_pages_count=related_count,
            total_chars=len(assembled_text),
            assembled_context=assembled_text,
            retrieved_pages=final_pages,
            status="retrieved"
        )

# Default singleton instance
retriever_service = IntelligentRetriever()
