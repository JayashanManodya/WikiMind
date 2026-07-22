from fastapi import APIRouter, File, UploadFile, HTTPException, status
from BackEnd.schemas import UploadResponse, ErrorDetail
from BackEnd.services.file_service import file_service

router = APIRouter(prefix="", tags=["File Upload"])

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Document",
    description="Upload raw documents (PDF, DOCX, TXT, MD) to the WikiMind storage for knowledge processing.",
    responses={
        400: {"model": ErrorDetail, "description": "Invalid file format or missing file"},
        500: {"model": ErrorDetail, "description": "Server error while saving file"}
    }
)
async def upload_document(file: UploadFile = File(..., description="Document file to upload (.pdf, .docx, .txt, .md)")):
    """
    Receives raw document file, validates extension, and saves it to local disk storage.
    Note: Document processing and AI vector generation will happen in subsequent phases.
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded. Please attach a valid file."
        )

    result = await file_service.save_file(file)
    return UploadResponse(**result)
