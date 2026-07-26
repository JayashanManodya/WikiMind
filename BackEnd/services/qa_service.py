import os
import re
from typing import List, Dict, Any, Optional, Set
from fastapi import HTTPException, status

from BackEnd.schemas import (
    QARequest,
    QAResponse,
    RetrievalContextResponse,
    RetrievedPageDetail
)
from BackEnd.services.retriever_service import retriever_service

REFUSAL_MESSAGE = "I cannot answer this question based on the stored knowledge base."

SYSTEM_PROMPT = """
You are WikiMind, an AI Knowledge Management Assistant.
Your task is to answer user questions using ONLY the provided Knowledge Base Context below.

STRICT GROUNDING INSTRUCTIONS:
1. Rely ONLY on the explicit facts directly stated in the context.
2. Do NOT invent, hallucinate, or extrapolate facts outside the context.
3. Include inline citations to source files (e.g. "[Tesla.md]", "[Elon_Musk.md]") after factual statements.
4. ZERO HALLUCINATION RULE: If the provided context does not contain enough information to answer the user's question, respond EXACTLY with:
   "I cannot answer this question based on the stored knowledge base."
"""

class QAService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def extract_citations(self, answer_text: str, available_filenames: List[str]) -> List[str]:
        """Extracts unique cited filenames from answer text (e.g., '[Tesla.md]' -> 'Tesla.md')"""
        found = set(re.findall(r'\[([a-zA-Z0-9_\-\.]+\.md)\]', answer_text))
        valid_citations = [f for f in available_filenames if f in found or f.replace(".md", "") in found]
        if not valid_citations and available_filenames and REFUSAL_MESSAGE not in answer_text:
            # Fallback to top primary file if answer is grounded but missed bracket syntax
            valid_citations = [available_filenames[0]]
        return sorted(list(set(valid_citations)))

    def answer_question_openai(self, question: str, retrieval_res: RetrievalContextResponse) -> QAResponse:
        """Executes grounded QA using LangChain LCEL Chain with Pydantic Structured Output"""
        from BackEnd.services.langchain_service import langchain_engine
        res = langchain_engine.answer_question_chain(question, retrieval_res.assembled_context)
        if res:
            return res
        return self.answer_question_deterministic(question, retrieval_res)

    def answer_question_deterministic(self, question: str, retrieval_res: RetrievalContextResponse) -> QAResponse:
        """
        Deterministic, offline Grounded QA engine.
        Synthesizes factual answers from retrieved wiki pages and enforces refusal when knowledge is absent.
        """
        q_lower = question.lower()
        q_words = set(re.findall(r'\b[a-z0-9_\-]{3,}\b', q_lower))
        stop_words = {
            "who", "what", "where", "when", "why", "how", "is", "are", "was", "were", 
            "the", "a", "an", "and", "or", "did", "does", "do", "tell", "me", "about",
            "which", "with", "from", "that", "this", "these", "those", "have", "has", "had"
        }
        keywords = [w for w in q_words if w not in stop_words]

        pages = retrieval_res.retrieved_pages
        filenames = [p.filename for p in pages]

        if not pages or not keywords:
            return QAResponse(
                question=question,
                answer=REFUSAL_MESSAGE,
                citations=[],
                confidence_score=0.0,
                grounded=False,
                retrieved_pages_count=0,
                context_summary="No relevant knowledge base pages found.",
                status="refused"
            )

        # Check if ALL major query keywords are completely missing from the context
        all_context_text = " ".join([p.content.lower() for p in pages])
        matched_keywords = [kw for kw in keywords if kw in all_context_text]
        
        # Refusal check: If less than 40% of non-stopword query keywords exist anywhere in retrieved context
        if not matched_keywords or (len(matched_keywords) / len(keywords)) < 0.4:
            return QAResponse(
                question=question,
                answer=REFUSAL_MESSAGE,
                citations=[],
                confidence_score=0.0,
                grounded=False,
                retrieved_pages_count=len(pages),
                context_summary=f"Knowledge base searched ({len(pages)} pages) but key terms in question were not found.",
                status="refused"
            )

        # Collect relevant sentences across retrieved pages
        matching_sentences: List[Tuple[str, str, float]] = []

        for page in pages:
            lines = page.content.splitlines()
            for line in lines:
                l_strip = line.strip()
                if not l_strip or l_strip.startswith("#") or l_strip.startswith("**Entity Type**"):
                    continue

                line_lower = l_strip.lower()
                matches = sum(1 for kw in keywords if kw in line_lower)
                if matches > 0:
                    score = matches / len(keywords)
                    matching_sentences.append((l_strip, page.filename, score))

        if not matching_sentences:
            return QAResponse(
                question=question,
                answer=REFUSAL_MESSAGE,
                citations=[],
                confidence_score=0.0,
                grounded=False,
                retrieved_pages_count=len(pages),
                context_summary=f"Knowledge base searched ({len(pages)} pages) but no facts matched the question.",
                status="refused"
            )

        # Sort matching sentences by relevance score descending
        matching_sentences.sort(key=lambda x: x[2], reverse=True)

        answer_parts: List[str] = []
        used_citations: Set[str] = set()

        for stmt, fn, score in matching_sentences[:4]:
            clean_stmt = stmt.lstrip("- ").strip()
            if not clean_stmt.endswith("."):
                clean_stmt += "."
            answer_parts.append(f"{clean_stmt} [{fn}]")
            used_citations.add(fn)

        final_answer = " ".join(answer_parts)
        citations_list = sorted(list(used_citations))

        return QAResponse(
            question=question,
            answer=final_answer,
            citations=citations_list,
            confidence_score=0.90,
            grounded=True,
            retrieved_pages_count=len(pages),
            context_summary=f"Synthesized from {len(citations_list)} wiki pages ({', '.join(citations_list)}).",
            status="answered"
        )

    def answer_question(self, question: str, top_k: int = 3, max_chars: int = 4000) -> QAResponse:
        """
        Main Orchestrator:
        1. Calls retriever_service.retrieve_multi_hop_context(question)
        2. Evaluates context relevance
        3. Calls OpenAI or offline deterministic QA synthesis
        """
        retrieval_res = retriever_service.retrieve_multi_hop_context(
            question=question,
            top_k=top_k,
            max_chars=max_chars
        )

        if self.api_key:
            return self.answer_question_openai(question, retrieval_res)
        else:
            return self.answer_question_deterministic(question, retrieval_res)

# Default singleton instance
qa_service = QAService()
