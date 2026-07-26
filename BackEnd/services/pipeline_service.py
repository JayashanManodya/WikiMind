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
        Executes the end-to-end background ingestion pipeline via LangGraph StateGraph:
        1. parse_node: Parse PDF/DOCX/TXT text pages
        2. clean_node: Clean text, unicode & footers
        3. extract_node: Extract entities, definitions, facts & relationships into SQLite DB
        4. wiki_node: Generate Wikipedia-style Markdown topic pages
        5. embed_node: Build & update vector embeddings in storage/vectors/index_vectors.json
        """
        from BackEnd.services.graph_service import graph_service
        return graph_service.run_ingestion_graph(file_id)

# Default singleton instance
pipeline_service = PipelineService()
