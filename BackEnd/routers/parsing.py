from fastapi import APIRouter, HTTPException, status
from BackEnd.schemas import ParsedDocumentResponse, ErrorDetail
from BackEnd.services.parser_service import parser_service

router = APIRouter(prefix="/documents", tags=["Document Parsing"])

@router.post(
    "/{file_id}/parse",
    response_model=ParsedDocumentResponse,
    summary="Parse Document Content",
    description="Parses document text page-by-page using PyMuPDF for PDFs or python-docx for Word files.",
    responses={
        404: {"model": ErrorDetail, "description": "Document or file not found"},
        500: {"model": ErrorDetail, "description": "Parsing error"}
    }
)
def parse_document(file_id: str):
    """Trigger document parsing by file_id"""
    return parser_service.parse_document(file_id)

@router.get(
    "/{file_id}/parsed",
    response_model=ParsedDocumentResponse,
    summary="Get Parsed Document Output",
    description="Retrieve previously stored parsed text output for a specific document ID.",
    responses={
        404: {"model": ErrorDetail, "description": "Parsed output not found"}
    }
)
def get_parsed_document(file_id: str):
    """Retrieve stored parsed JSON output by file_id"""
    parsed_doc = parser_service.get_parsed_document(file_id)
    if not parsed_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parsed output for file_id '{file_id}' not found. Please trigger POST /documents/{file_id}/parse first."
        )
    return parsed_doc
