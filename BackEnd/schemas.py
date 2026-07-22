from pydantic import BaseModel, Field

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

class UploadResponse(BaseModel):
    file_id: str = Field(..., json_schema_extra={"example": "f47ac10b-58cc-4372-a567-0e02b2c3d479"})
    filename: str = Field(..., json_schema_extra={"example": "sample_document.pdf"})
    content_type: str = Field(..., json_schema_extra={"example": "application/pdf"})
    size_bytes: int = Field(..., json_schema_extra={"example": 1048576})
    saved_path: str = Field(..., json_schema_extra={"example": "./storage/uploads/f47ac10b_sample_document.pdf"})
    status: str = Field(default="uploaded", json_schema_extra={"example": "uploaded"})
    message: str = Field(..., json_schema_extra={"example": "File successfully uploaded and stored."})

class ErrorDetail(BaseModel):
    detail: str = Field(..., json_schema_extra={"example": "Unsupported file format '.exe'. Allowed formats: .docx, .md, .pdf, .txt"})
    error_code: str = Field(default="INVALID_FILE_TYPE", json_schema_extra={"example": "INVALID_FILE_TYPE"})
