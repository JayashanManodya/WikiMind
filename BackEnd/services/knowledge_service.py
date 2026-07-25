import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status

from BackEnd.schemas import (
    KnowledgeExtractionResponse,
    ExtractedEntity,
    ExtractedDefinition,
    ExtractedFact,
    ExtractedRelationship
)
from BackEnd.services.cleaner_service import cleaner_service
from BackEnd.services.metadata_service import metadata_service
from BackEnd.services.llm_service import llm_service

BACKEND_DIR = Path(__file__).resolve().parent.parent

class KnowledgeService:
    def __init__(self, knowledge_dir: str = "./BackEnd/storage/knowledge"):
        if isinstance(knowledge_dir, str) and knowledge_dir.startswith("./"):
            clean_rel = knowledge_dir[2:]
            if clean_rel.startswith("BackEnd/"):
                self.knowledge_dir = (BACKEND_DIR.parent / clean_rel).resolve()
            else:
                self.knowledge_dir = (BACKEND_DIR / "storage" / clean_rel.replace("storage/", "")).resolve()
        else:
            self.knowledge_dir = Path(knowledge_dir).resolve()
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

    def extract_knowledge_for_document(self, file_id: str) -> KnowledgeExtractionResponse:
        """
        Main Orchestrator: Fetches cleaned document text, passes it to LLMService,
        constructs KnowledgeExtractionResponse, persists JSON artifact to storage/knowledge/,
        and updates metadata status to 'extracted'.
        """
        # Step 1: Ensure cleaned document text is available
        cleaned_doc = cleaner_service.get_cleaned_document(file_id)
        if not cleaned_doc:
            cleaned_doc = cleaner_service.clean_document(file_id)

        input_text = cleaned_doc.full_cleaned_text
        if not input_text or len(input_text.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document text is empty; cannot extract knowledge."
            )

        # Step 2: Extract knowledge via LLM or deterministic engine
        raw_extraction = llm_service.extract_knowledge(input_text)

        # Step 3: Convert to Pydantic objects
        entities = [ExtractedEntity(**e) for e in raw_extraction.get("entities", [])]
        definitions = [ExtractedDefinition(**d) for d in raw_extraction.get("definitions", [])]
        facts = [ExtractedFact(**f) for f in raw_extraction.get("facts", [])]
        relationships = [ExtractedRelationship(**r) for r in raw_extraction.get("relationships", [])]
        summary = raw_extraction.get("summary", "Knowledge extraction complete.")

        knowledge_response = KnowledgeExtractionResponse(
            file_id=cleaned_doc.file_id,
            original_filename=cleaned_doc.original_filename,
            summary=summary,
            entities=entities,
            definitions=definitions,
            facts=facts,
            relationships=relationships,
            extracted_at=datetime.now(timezone.utc).isoformat(),
            status="extracted"
        )

        # Step 4: Persist JSON artifact
        json_path = self.knowledge_dir / f"{file_id}_knowledge.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(knowledge_response.model_dump_json(indent=2))

        # Step 5: Sync Knowledge entities, definitions, facts, relationships to Database
        try:
            from BackEnd.services.db_service import db_service
            db_service.save_knowledge(knowledge_response)
        except Exception:
            pass

        # Step 6: Update document metadata status
        metadata = metadata_service.get_metadata_by_id(file_id)
        if metadata:
            metadata.status = "extracted"
            metadata_service.save_metadata(metadata)

        return knowledge_response

    def get_knowledge_document(self, file_id: str) -> Optional[KnowledgeExtractionResponse]:
        """Retrieve stored knowledge extraction response JSON if available"""
        json_path = self.knowledge_dir / f"{file_id}_knowledge.json"
        if not json_path.exists():
            return None
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return KnowledgeExtractionResponse(**data)
        except Exception:
            return None

# Default singleton instance
knowledge_service = KnowledgeService()
