from fastapi import APIRouter, HTTPException, status
from BackEnd.schemas import DocumentMetadata, DocumentListResponse, ErrorDetail
from BackEnd.services.metadata_service import metadata_service

router = APIRouter(prefix="/documents", tags=["Documents Management"])

@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List Uploaded Documents",
    description="Retrieve metadata for all stored documents in the system."
)
def list_documents():
    docs = metadata_service.get_all_metadata()
    return DocumentListResponse(
        total_documents=len(docs),
        documents=docs
    )

@router.get(
    "/{file_id}",
    response_model=DocumentMetadata,
    summary="Get Document Metadata by ID",
    description="Retrieve document metadata details for a specific file UUID.",
    responses={
        404: {"model": ErrorDetail, "description": "Document not found"}
    }
)
def get_document(file_id: str):
    doc = metadata_service.get_metadata_by_id(file_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with file_id '{file_id}' not found."
        )
    return doc
