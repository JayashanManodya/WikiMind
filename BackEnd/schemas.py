from pydantic import BaseModel, Field
from typing import List, Optional

class RootResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "online"})
    app: str = Field(..., json_schema_extra={"example": "WikiMind"})
    environment: str = Field(..., json_schema_extra={"example": "development"})
    message: str = Field(..., json_schema_extra={"example": "Welcome to WikiMind Knowledge Management System API"})

class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    storage_dir: str = Field(..., json_schema_extra={"example": "./storage"})
    wiki_dir: str = Field(..., json_schema_extra={"example": "./wiki"})
    llm_provider: str = Field(..., json_schema_extra={"example": "openai"})
    storage_accessible: bool = Field(default=True, json_schema_extra={"example": True})

class DocumentMetadata(BaseModel):
    file_id: str = Field(..., json_schema_extra={"example": "f47ac10b-58cc-4372-a567-0e02b2c3d479"})
    original_filename: str = Field(..., json_schema_extra={"example": "sample_document.pdf"})
    stored_filename: str = Field(..., json_schema_extra={"example": "f47ac10b-58cc-4372-a567-0e02b2c3d479_sample_document.pdf"})
    file_path: str = Field(..., json_schema_extra={"example": "./documents/f47ac10b-58cc-4372-a567-0e02b2c3d479_sample_document.pdf"})
    content_type: str = Field(..., json_schema_extra={"example": "application/pdf"})
    size_bytes: int = Field(..., json_schema_extra={"example": 1048576})
    sha256_hash: str = Field(..., json_schema_extra={"example": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"})
    uploaded_at: str = Field(..., json_schema_extra={"example": "2026-07-22T18:00:00Z"})
    status: str = Field(default="stored", json_schema_extra={"example": "stored"})

class UploadResponse(BaseModel):
    file_id: str = Field(..., json_schema_extra={"example": "f47ac10b-58cc-4372-a567-0e02b2c3d479"})
    filename: str = Field(..., json_schema_extra={"example": "sample_document.pdf"})
    content_type: str = Field(..., json_schema_extra={"example": "application/pdf"})
    size_bytes: int = Field(..., json_schema_extra={"example": 1048576})
    saved_path: str = Field(..., json_schema_extra={"example": "./documents/f47ac10b_sample_document.pdf"})
    status: str = Field(default="uploaded", json_schema_extra={"example": "uploaded"})
    message: str = Field(..., json_schema_extra={"example": "File successfully uploaded and stored."})
    metadata: Optional[DocumentMetadata] = None

class DocumentListResponse(BaseModel):
    total_documents: int = Field(..., json_schema_extra={"example": 5})
    documents: List[DocumentMetadata]

class ErrorDetail(BaseModel):
    detail: str = Field(..., json_schema_extra={"example": "Unsupported file format '.exe'. Allowed formats: .docx, .md, .pdf, .txt"})
    error_code: str = Field(default="INVALID_FILE_TYPE", json_schema_extra={"example": "INVALID_FILE_TYPE"})
