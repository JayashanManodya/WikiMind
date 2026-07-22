import os
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from BackEnd.schemas import DocumentMetadata
from BackEnd.services.metadata_service import metadata_service

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

class FileService:
    def __init__(self, base_documents_dir: str = "./documents"):
        self.documents_dir = Path(base_documents_dir)
        self.documents_dir.mkdir(parents=True, exist_ok=True)

    def is_valid_file_extension(self, filename: str) -> bool:
        """Check if file has an allowed extension"""
        if not filename:
            return False
        ext = Path(filename).suffix.lower()
        return ext in ALLOWED_EXTENSIONS

    async def save_file(self, file: UploadFile) -> dict:
        """
        Validate file extension & size, stream file in chunks to documents/ with UUID naming,
        calculate SHA256 hash, and store metadata record.
        """
        if not file.filename or not self.is_valid_file_extension(file.filename):
            ext = Path(file.filename).suffix if file.filename else "unknown"
            allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {allowed_str}"
            )

        file_id = str(uuid.uuid4())
        safe_original_name = Path(file.filename).name
        stored_filename = f"{file_id}_{safe_original_name}"
        saved_path = self.documents_dir / stored_filename

        total_bytes = 0
        sha256_hash = hashlib.sha256()
        chunk_size = 1024 * 1024  # 1MB chunk size

        try:
            with open(saved_path, "wb") as buffer:
                while chunk := await file.read(chunk_size):
                    buffer.write(chunk)
                    sha256_hash.update(chunk)
                    total_bytes += len(chunk)

            # Check for 0-byte / empty files
            if total_bytes == 0:
                if saved_path.exists():
                    saved_path.unlink()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty (0 bytes)."
                )

        except HTTPException:
            raise
        except Exception as e:
            if saved_path.exists():
                saved_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save document: {str(e)}"
            )
        finally:
            await file.seek(0)  # Reset pointer for potential downstream re-use

        calculated_hash = sha256_hash.hexdigest()
        uploaded_at_iso = datetime.now(timezone.utc).isoformat()

        # Create structured metadata record
        metadata_record = DocumentMetadata(
            file_id=file_id,
            original_filename=safe_original_name,
            stored_filename=stored_filename,
            file_path=str(saved_path),
            content_type=file.content_type or "application/octet-stream",
            size_bytes=total_bytes,
            sha256_hash=calculated_hash,
            uploaded_at=uploaded_at_iso,
            status="stored"
        )

        # Persist metadata entry
        metadata_service.save_metadata(metadata_record)

        return {
            "file_id": file_id,
            "filename": safe_original_name,
            "content_type": file.content_type or "application/octet-stream",
            "size_bytes": total_bytes,
            "saved_path": str(saved_path),
            "status": "uploaded",
            "message": f"Document '{safe_original_name}' successfully stored.",
            "metadata": metadata_record
        }

# Default singleton instance
file_service = FileService()
