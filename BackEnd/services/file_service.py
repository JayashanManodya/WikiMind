import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "application/octet-stream"  # Allowed for fallback compatibility
}

class FileService:
    def __init__(self, base_storage_dir: str = "./storage"):
        self.upload_dir = Path(base_storage_dir) / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def is_valid_file(self, filename: str) -> bool:
        """Check if file has an allowed extension"""
        if not filename:
            return False
        ext = Path(filename).suffix.lower()
        return ext in ALLOWED_EXTENSIONS

    async def save_file(self, file: UploadFile) -> dict:
        """
        Validate and save uploaded file using streaming chunks to handle large files.
        Returns metadata tuple (file_id, filename, content_type, size_bytes, saved_path).
        """
        if not file.filename or not self.is_valid_file(file.filename):
            ext = Path(file.filename).suffix if file.filename else "unknown"
            allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {allowed_str}"
            )

        file_id = str(uuid.uuid4())
        safe_filename = Path(file.filename).name
        saved_filename = f"{file_id}_{safe_filename}"
        saved_path = self.upload_dir / saved_filename

        total_bytes = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        try:
            with open(saved_path, "wb") as buffer:
                while chunk := await file.read(chunk_size):
                    buffer.write(chunk)
                    total_bytes += len(chunk)
        except Exception as e:
            if saved_path.exists():
                saved_path.unlink()
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        finally:
            await file.seek(0)  # Reset file pointer if needed

        return {
            "file_id": file_id,
            "filename": safe_filename,
            "content_type": file.content_type or "application/octet-stream",
            "size_bytes": total_bytes,
            "saved_path": str(saved_path),
            "status": "uploaded",
            "message": f"File '{safe_filename}' successfully uploaded and stored."
        }

# Default singleton instance
file_service = FileService()
