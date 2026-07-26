from fastapi import APIRouter, File, UploadFile, Query, HTTPException, status
from BackEnd.schemas import UploadResponse, ErrorDetail
from BackEnd.services.file_service import file_service
from BackEnd.services.pipeline_service import pipeline_service

router = APIRouter(prefix="", tags=["File Upload"])

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Document",
    description="Upload raw documents (PDF, DOCX, TXT, MD) to the WikiMind storage. Set auto_process=true for automated background ingestion pipeline.",
    responses={
        400: {"model": ErrorDetail, "description": "Invalid file format or missing file"},
        500: {"model": ErrorDetail, "description": "Server error while saving file"}
    }
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (.pdf, .docx, .txt, .md)"),
    auto_process: bool = Query(True, description="When true, automatically executes full background ingestion (parse, clean, extract DB, wiki generate, vector index)")
):
    """
    Receives raw document file, validates extension, saves to storage, and optionally triggers full background ingestion.
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded. Please attach a valid file."
        )

    result = await file_service.save_file(file)
    file_id = result["file_id"]

    # Option A: Immediate Background Ingestion
    if auto_process:
        try:
            pipeline_service.process_document_pipeline(file_id)
            result["message"] = f"File successfully uploaded and fully ingested into Wiki Knowledge Base and Vector Store."
            result["status"] = "fully_processed"
        except Exception as e:
            # Keep uploaded status if pipeline error occurs
            pass

    return UploadResponse(**result)
