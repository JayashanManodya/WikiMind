import os
import re
import json
from typing import Dict, List, Any, Optional
from BackEnd.schemas import (
    ExtractedEntity,
    ExtractedDefinition,
    ExtractedFact,
    ExtractedRelationship
)

from BackEnd.prompts import SYSTEM_EXTRACTION_PROMPT

SYSTEM_PROMPT = """
You are an expert AI Knowledge Extraction Engine for WikiMind.
Your task is to analyze document text and extract structured domain knowledge in JSON format.

Extraction Instructions:
1. ENTITIES: Extract major named entities (PERSON, ORGANIZATION, CONCEPT, TECHNOLOGY, PRODUCT).
2. DEFINITIONS: Extract clear definitions or explanations of terms.
3. FACTS: Extract core factual claims and verified statements.
4. RELATIONSHIPS: Extract typed directional relationships between entities (e.g., EntityA --[FOUNDED_BY]--> EntityB).
5. SUMMARY: Provide a concise executive summary of the document.

Return ONLY a JSON object with this exact structure:
{
  "summary": "Executive summary...",
  "entities": [
    {"name": "...", "type": "ORGANIZATION", "description": "..."}
  ],
  "definitions": [
    {"term": "...", "definition": "..."}
  ],
  "facts": [
    {"fact": "...", "confidence": 0.95, "source_section": "Page 1"}
  ],
  "relationships": [
    {"source_entity": "...", "relation": "FOUNDED_BY", "target_entity": "...", "description": "..."}
  ]
}
"""

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def extract_knowledge_with_llm(self, text: str) -> Dict[str, Any]:
        """Calls LangChain LCEL Chain (prompt | llm | parser) for Knowledge Extraction"""
        from BackEnd.services.langchain_service import langchain_engine
        return langchain_engine.extract_knowledge_chain(text)

    def extract_knowledge_deterministic(self, text: str) -> Dict[str, Any]:
        """
        Deterministic, offline NLP & regex extraction engine for testing and fallback.
        Parses entities, relationships (e.g. 'founded by', 'created by', 'uses'), definitions, facts, and summary.
        """
        entities: List[Dict[str, str]] = []
        relationships: List[Dict[str, str]] = []
        definitions: List[Dict[str, str]] = []
        facts: List[Dict[str, Any]] = []

        seen_entities = set()
        seen_relationships = set()

        # 1. Relationship Pattern Regex Rules
        rel_patterns = [
            (r'([A-Z][a-zA-Z0-9_\-\s]+?)\s+was\s+founded\s+by\s+([A-Z][a-zA-Z0-9_\-]+(?:\s+[A-Z][a-zA-Z0-9_\-]+)*)(?:\s+in\s+(\d{4}))?', "FOUNDED_BY"),
            (r'([A-Z][a-zA-Z0-9_\-\s]+?)\s+is\s+founded\s+by\s+([A-Z][a-zA-Z0-9_\-]+(?:\s+[A-Z][a-zA-Z0-9_\-]+)*)(?:\s+in\s+(\d{4}))?', "FOUNDED_BY"),
            (r'([A-Z][a-zA-Z0-9_\-\s]+?)\s+was\s+created\s+by\s+([A-Z][a-zA-Z0-9_\-]+(?:\s+[A-Z][a-zA-Z0-9_\-]+)*)', "CREATED_BY"),
            (r'([A-Z][a-zA-Z0-9_\-\s]+?)\s+created\s+by\s+([A-Z][a-zA-Z0-9_\-]+(?:\s+[A-Z][a-zA-Z0-9_\-]+)*)', "CREATED_BY"),
            (r'([A-Z][a-zA-Z0-9_\-\s]+?)\s+uses\s+([A-Z][a-zA-Z0-9_\-]+(?:\s+[A-Z][a-zA-Z0-9_\-]+)*)', "USES"),
            (r'([A-Z][a-zA-Z0-9_\-\s]+?)\s+is\s+a\s+([a-zA-Z0-9_\-\s]+?)(?:[\.,\n]|$)', "IS_A"),
        ]

        for pattern, rel_type in rel_patterns:
            matches = re.finditer(pattern, text)
            for m in matches:
                source = m.group(1).strip()
                target = m.group(2).strip()
                year = m.group(3) if len(m.groups()) >= 3 and m.group(3) else None
                
                if source and target and len(source) > 1 and len(target) > 1:
                    rel_key = f"{source}:{rel_type}:{target}"
                    if rel_key not in seen_relationships:
                        seen_relationships.add(rel_key)
                        desc = f"{source} is connected to {target} via {rel_type}."
                        if year:
                            desc += f" (Year: {year})"
                            
                        relationships.append({
                            "source_entity": source,
                            "relation": rel_type,
                            "target_entity": target,
                            "description": desc
                        })
                        
                        # Auto register entities
                        if source not in seen_entities:
                            seen_entities.add(source)
                            entities.append({"name": source, "type": "ORGANIZATION" if rel_type == "FOUNDED_BY" else "CONCEPT", "description": f"Entity extracted from text."})
                        if target not in seen_entities:
                            seen_entities.add(target)
                            entities.append({"name": target, "type": "PERSON" if rel_type in ("FOUNDED_BY", "CREATED_BY") else "TECHNOLOGY", "description": f"Entity extracted from text."})

        # 2. Definition Pattern Regex Rules
        def_patterns = [
            r'([A-Z][a-zA-Z0-9_\-\s]{2,30})\s+is\s+defined\s+as\s+([^.\n]+)',
            r'([A-Z][a-zA-Z0-9_\-\s]{2,30})\s+is\s+a\s+([^.\n]+(?:component|system|architecture|platform|tool|engine|model|process|framework))',
            r'([A-Z][a-zA-Z0-9_\-\s]{2,30}):\s+([^.\n]+)'
        ]
        for pattern in def_patterns:
            matches = re.finditer(pattern, text)
            for m in matches:
                term = m.group(1).strip()
                definition = m.group(2).strip()
                if term and definition and len(term) > 2 and len(definition) > 10:
                    definitions.append({
                        "term": term,
                        "definition": definition
                    })
                    if term not in seen_entities:
                        seen_entities.add(term)
                        entities.append({"name": term, "type": "CONCEPT", "description": definition})

        # 3. Capitalized Proper Nouns Extraction for Entities
        capitalized_words = re.findall(r'\b([A-Z][a-zA-B0-9_\-]{2,}(?:\s+[A-Z][a-zA-B0-9_\-]{2,})*)\b', text)
        stopwords = {"Page", "The", "This", "Section", "Knowledge", "Extraction", "System", "API", "Document", "First", "Second", "Third"}
        for word in capitalized_words:
            if word not in seen_entities and word not in stopwords and len(word) > 2:
                seen_entities.add(word)
                e_type = "PERSON" if " " in word else "CONCEPT"
                entities.append({
                    "name": word,
                    "type": e_type,
                    "description": f"Extracted domain entity ({word})."
                })

        # 4. Fact Extraction (Factual Sentences)
        sentences = [s.strip() for s in re.split(r'[.\n]', text) if len(s.strip()) > 15]
        for idx, sentence in enumerate(sentences[:10]):  # Top 10 facts
            facts.append({
                "fact": sentence if sentence.endswith('.') else f"{sentence}.",
                "confidence": 0.95,
                "source_section": f"Section {(idx // 3) + 1}"
            })

        # 5. Summary Generation
        if sentences:
            summary = " ".join([s if s.endswith('.') else f"{s}." for s in sentences[:3]])
        else:
            summary = "Extracted structured knowledge representation."

        return {
            "summary": summary,
            "entities": entities,
            "definitions": definitions,
            "facts": facts,
            "relationships": relationships
        }

    def filter_hallucinations(self, extraction: Dict[str, Any], text: str) -> Dict[str, Any]:
        """
        Validates that extracted entity names and relationship nodes are grounded in the source text.
        Filters out entities or relationships referencing terms/names not present in the source text.
        """
        if not text:
            return extraction
            
        lower_text = text.lower()
        valid_entities = []
        valid_names = set()

        for entity in extraction.get("entities", []):
            name = entity.get("name", "").strip()
            if name and (name.lower() in lower_text or any(token.lower() in lower_text for token in name.split() if len(token) > 2)):
                valid_entities.append(entity)
                valid_names.add(name)

        valid_relationships = []
        for rel in extraction.get("relationships", []):
            source = rel.get("source_entity", "").strip()
            target = rel.get("target_entity", "").strip()
            if (source and (source.lower() in lower_text or source in valid_names)) and \
               (target and (target.lower() in lower_text or target in valid_names)):
                valid_relationships.append(rel)

        extraction["entities"] = valid_entities
        extraction["relationships"] = valid_relationships
        return extraction

    def extract_knowledge(self, text: str) -> Dict[str, Any]:
        """Main entry point: Calls OpenAI LLM if OPENAI_API_KEY is configured, else uses fallback, then filters hallucinations"""
        if self.api_key:
            raw_extraction = self.extract_knowledge_with_llm(text)
        else:
            raw_extraction = self.extract_knowledge_deterministic(text)
            
        return self.filter_hallucinations(raw_extraction, text)

# Default singleton instance
llm_service = LLMService()
