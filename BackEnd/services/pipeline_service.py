from typing import Dict, Any
from fastapi import HTTPException, status

from BackEnd.schemas import FullPipelineResponse
from BackEnd.services.parser_service import parser_service
from BackEnd.services.cleaner_service import cleaner_service
from BackEnd.services.knowledge_service import knowledge_service
from BackEnd.services.wiki_service import wiki_service
from BackEnd.services.vector_service import vector_service

class PipelineService:
    def __init__(self):
        pass

    def process_document_pipeline(self, file_id: str) -> FullPipelineResponse:
        """
        Executes the end-to-end background ingestion pipeline:
        1. Parse PDF/DOCX/TXT text pages
        2. Clean text, unicode & footers
        3. Extract entities, definitions, facts & relationships into SQLite DB
        4. Generate Wikipedia-style Markdown topic pages
        5. Build & update vector embeddings in storage/vectors/index_vectors.json
        """
        # Step 1: Parse Document
        parsed_res = parser_service.parse_document(file_id)

        # Step 2: Clean Text
        cleaned_res = cleaner_service.clean_document(file_id)

        # Step 3: Extract Knowledge & Save SQLite Database
        knowledge_res = knowledge_service.extract_knowledge_for_document(file_id)

        # Step 4: Generate Wiki Markdown Pages
        wiki_res = wiki_service.generate_wiki_for_document(file_id)

        # Step 5: Index Vector Store
        vector_res = vector_service.index_all_wiki_pages()

        return FullPipelineResponse(
            file_id=file_id,
            filename=parsed_res.original_filename,
            total_pages=parsed_res.total_pages,
            entities_extracted=len(knowledge_res.entities),
            wiki_pages_generated=wiki_res.total_pages_generated,
            vector_indexed=True,
            status="fully_processed",
            message=f"Document '{parsed_res.original_filename}' successfully ingested, parsed, cleaned, extracted into DB, generated {wiki_res.total_pages_generated} wiki pages, and vector indexed."
        )

# Default singleton instance
pipeline_service = PipelineService()
