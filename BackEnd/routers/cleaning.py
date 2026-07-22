from fastapi import APIRouter, HTTPException, status
from BackEnd.schemas import CleanedDocumentResponse, ErrorDetail
from BackEnd.services.cleaner_service import cleaner_service

router = APIRouter(prefix="/documents", tags=["Text Preprocessing & Cleaning"])

@router.post(
    "/{file_id}/clean",
    response_model=CleanedDocumentResponse,
    summary="Clean Document Text",
    description="Preprocesses parsed document text: normalizes unicode, collapses extra whitespace, strips page numbers, and removes repetitive running headers/footers.",
    responses={
        404: {"model": ErrorDetail, "description": "Document or parsed text not found"},
        500: {"model": ErrorDetail, "description": "Cleaning error"}
    }
)
def clean_document(file_id: str):
    """Trigger text cleaning pipeline for document file_id"""
    return cleaner_service.clean_document(file_id)

@router.get(
    "/{file_id}/cleaned",
    response_model=CleanedDocumentResponse,
    summary="Get Cleaned Document Text",
    description="Retrieve stored cleaned document output for a specific document ID.",
    responses={
        404: {"model": ErrorDetail, "description": "Cleaned document output not found"}
    }
)
def get_cleaned_document(file_id: str):
    """Retrieve stored cleaned JSON output by file_id"""
    cleaned_doc = cleaner_service.get_cleaned_document(file_id)
    if not cleaned_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cleaned output for file_id '{file_id}' not found. Please trigger POST /documents/{file_id}/clean first."
        )
    return cleaned_doc
