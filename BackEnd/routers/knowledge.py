from fastapi import APIRouter, HTTPException, status
from BackEnd.schemas import KnowledgeExtractionResponse, ErrorDetail
from BackEnd.services.knowledge_service import knowledge_service

router = APIRouter(prefix="/documents", tags=["Knowledge Extraction Engine"])

@router.post(
    "/{file_id}/extract-knowledge",
    response_model=KnowledgeExtractionResponse,
    summary="Extract Structured Knowledge",
    description="Analyzes document text and extracts structured Entities, Definitions, Facts, Relationships, and Executive Summary into JSON.",
    responses={
        404: {"model": ErrorDetail, "description": "Document not found"},
        500: {"model": ErrorDetail, "description": "Extraction error"}
    }
)
def extract_knowledge(file_id: str):
    """Trigger AI Knowledge Extraction pipeline for document file_id"""
    return knowledge_service.extract_knowledge_for_document(file_id)

@router.get(
    "/{file_id}/knowledge",
    response_model=KnowledgeExtractionResponse,
    summary="Get Extracted Knowledge Artifact",
    description="Retrieve stored knowledge extraction JSON artifact for a specific document ID.",
    responses={
        404: {"model": ErrorDetail, "description": "Knowledge artifact not found"}
    }
)
def get_knowledge(file_id: str):
    """Retrieve stored knowledge JSON output by file_id"""
    knowledge_doc = knowledge_service.get_knowledge_document(file_id)
    if not knowledge_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge artifact for file_id '{file_id}' not found. Please trigger POST /documents/{file_id}/extract-knowledge first."
        )
    return knowledge_doc
