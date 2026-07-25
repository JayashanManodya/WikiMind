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

class ParsedPage(BaseModel):
    page_number: int = Field(..., json_schema_extra={"example": 1})
    text: str = Field(..., json_schema_extra={"example": "Extracted text content from page 1."})
    char_count: int = Field(..., json_schema_extra={"example": 1250})

class ParsedDocumentResponse(BaseModel):
    file_id: str = Field(..., json_schema_extra={"example": "f47ac10b-58cc-4372-a567-0e02b2c3d479"})
    original_filename: str = Field(..., json_schema_extra={"example": "sample_document.pdf"})
    total_pages: int = Field(..., json_schema_extra={"example": 5})
    full_text: str = Field(..., json_schema_extra={"example": "Complete extracted plain text with page dividers."})
    pages: List[ParsedPage]
    parsed_at: str = Field(..., json_schema_extra={"example": "2026-07-22T18:05:00Z"})
    status: str = Field(default="parsed", json_schema_extra={"example": "parsed"})

class CleanedPage(BaseModel):
    page_number: int = Field(..., json_schema_extra={"example": 1})
    raw_char_count: int = Field(..., json_schema_extra={"example": 1400})
    cleaned_char_count: int = Field(..., json_schema_extra={"example": 1250})
    cleaned_text: str = Field(..., json_schema_extra={"example": "Cleaned text for page 1."})

class CleanedDocumentResponse(BaseModel):
    file_id: str = Field(..., json_schema_extra={"example": "f47ac10b-58cc-4372-a567-0e02b2c3d479"})
    original_filename: str = Field(..., json_schema_extra={"example": "sample_document.pdf"})
    total_pages: int = Field(..., json_schema_extra={"example": 5})
    full_cleaned_text: str = Field(..., json_schema_extra={"example": "Cleaned text with extra spaces, headers, and page numbers removed."})
    pages: List[CleanedPage]
    cleaned_at: str = Field(..., json_schema_extra={"example": "2026-07-22T18:10:00Z"})
    status: str = Field(default="cleaned", json_schema_extra={"example": "cleaned"})

# --- Phase 7 Knowledge Extraction Models ---

class ExtractedEntity(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Tesla"})
    type: str = Field(..., json_schema_extra={"example": "ORGANIZATION"})
    description: str = Field(..., json_schema_extra={"example": "Electric vehicle and clean energy company founded by Elon Musk."})

class ExtractedDefinition(BaseModel):
    term: str = Field(..., json_schema_extra={"example": "Knowledge Graph"})
    definition: str = Field(..., json_schema_extra={"example": "A structured representation of entities and relationships."})

class ExtractedFact(BaseModel):
    fact: str = Field(..., json_schema_extra={"example": "Tesla was founded by Elon Musk in 2003."})
    confidence: float = Field(default=0.95, json_schema_extra={"example": 0.95})
    source_section: Optional[str] = Field(None, json_schema_extra={"example": "Section 1"})

class ExtractedRelationship(BaseModel):
    source_entity: str = Field(..., json_schema_extra={"example": "Tesla"})
    relation: str = Field(..., json_schema_extra={"example": "FOUNDED_BY"})
    target_entity: str = Field(..., json_schema_extra={"example": "Elon Musk"})
    description: str = Field(..., json_schema_extra={"example": "Elon Musk co-founded Tesla Motors."})

class KnowledgeExtractionResponse(BaseModel):
    file_id: str = Field(..., json_schema_extra={"example": "f47ac10b-58cc-4372-a567-0e02b2c3d479"})
    original_filename: str = Field(..., json_schema_extra={"example": "sample_document.pdf"})
    summary: str = Field(..., json_schema_extra={"example": "Overview of Tesla's founding and core technological architecture."})
    entities: List[ExtractedEntity]
    definitions: List[ExtractedDefinition]
    facts: List[ExtractedFact]
    relationships: List[ExtractedRelationship]
    extracted_at: str = Field(..., json_schema_extra={"example": "2026-07-22T18:20:00Z"})
    status: str = Field(default="extracted", json_schema_extra={"example": "extracted"})

# --- Phase 8 Wiki Generation Models ---

class WikiPageSummary(BaseModel):
    entity_name: str = Field(..., json_schema_extra={"example": "Tesla"})
    filename: str = Field(..., json_schema_extra={"example": "Tesla.md"})
    entity_type: str = Field(..., json_schema_extra={"example": "ORGANIZATION"})
    link_count: int = Field(default=0, json_schema_extra={"example": 3})
    updated_at: str = Field(..., json_schema_extra={"example": "2026-07-25T20:00:00Z"})

class WikiPageResponse(BaseModel):
    entity_name: str = Field(..., json_schema_extra={"example": "Tesla"})
    filename: str = Field(..., json_schema_extra={"example": "Tesla.md"})
    entity_type: str = Field(..., json_schema_extra={"example": "ORGANIZATION"})
    content: str = Field(..., json_schema_extra={"example": "# Tesla\n\n**Type**: ORGANIZATION\n\n## Overview\n..."})
    links_to: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Elon Musk", "Electric Vehicles"]})
    created_at: str = Field(..., json_schema_extra={"example": "2026-07-25T20:00:00Z"})
    status: str = Field(default="generated", json_schema_extra={"example": "generated"})

class WikiIndexResponse(BaseModel):
    total_pages: int = Field(..., json_schema_extra={"example": 12})
    pages: List[WikiPageSummary]

class WikiGenerationResponse(BaseModel):
    file_id: str = Field(..., json_schema_extra={"example": "f47ac10b-58cc-4372-a567-0e02b2c3d479"})
    total_pages_generated: int = Field(..., json_schema_extra={"example": 3})
    pages_generated: List[WikiPageSummary]
    status: str = Field(default="wiki_generated", json_schema_extra={"example": "wiki_generated"})
    message: str = Field(..., json_schema_extra={"example": "Successfully generated wiki pages from document knowledge."})

class ErrorDetail(BaseModel):
    detail: str = Field(..., json_schema_extra={"example": "Unsupported file format '.exe'. Allowed formats: .docx, .md, .pdf, .txt"})
    error_code: str = Field(default="INVALID_FILE_TYPE", json_schema_extra={"example": "INVALID_FILE_TYPE"})
