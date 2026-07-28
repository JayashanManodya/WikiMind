"""FastAPI entry point for the WikiLLM System."""

import uuid
import json
import traceback as _traceback
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from .models import QuestionRequest, QAResponse
from .services.qa_service import answer_question
from .core.ingestion.parser import parse_document_bytes
from .core.ingestion.cleaner import clean_text
from .core.ingestion.wiki_generator import generate_wiki_pages_from_text
from .core.retrieval.vector_store import index_wiki_documents, index_documents_from_bytes

app = FastAPI(
    title="WikiLLM Intelligent Knowledge Management System",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory document storage store (file_id -> dict)
DOCUMENT_STORE: Dict[str, Dict[str, Any]] = {}
WIKI_DIR = Path("wiki")
UPLOAD_DIR = Path("backend/data/uploads")


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    auto_process: bool = Query(True)
):
    """Upload PDF, DOCX, TXT, or MD file and optionally run full WikiLLM ingestion pipeline."""
    allowed_exts = [".pdf", ".docx", ".doc", ".txt", ".md"]
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(allowed_exts)}"
        )

    try:
        file_bytes = await file.read()
        file_id = str(uuid.uuid4())
        size_bytes = len(file_bytes)

        # Save to upload dir
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        saved_file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        saved_file_path.write_bytes(file_bytes)

        doc_record = {
            "file_id": file_id,
            "filename": file.filename,
            "saved_path": str(saved_file_path),
            "size_bytes": size_bytes,
            "file_bytes": file_bytes,
            "status": "uploaded",
            "parsed_data": None,
            "cleaned_text": None,
            "wiki_pages": [],
            "vector_indexed": False
        }
        DOCUMENT_STORE[file_id] = doc_record

        if auto_process:
            # 1. Parse
            parsed = parse_document_bytes(file_bytes, file.filename)
            doc_record["parsed_data"] = parsed

            # 2. Clean
            cleaned = clean_text(parsed["full_text"])
            doc_record["cleaned_text"] = cleaned

            # 3. Wiki Generation
            wiki_pages = generate_wiki_pages_from_text(cleaned, file.filename, wiki_dir=str(WIKI_DIR))
            doc_record["wiki_pages"] = wiki_pages

            # 4. Vector Indexing (Full Wiki Markdown documents)
            num_indexed = index_wiki_documents(wiki_pages)
            doc_record["vector_indexed"] = True
            doc_record["status"] = "fully_processed"

            return {
                "file_id": file_id,
                "filename": file.filename,
                "saved_path": str(saved_file_path),
                "size_bytes": size_bytes,
                "message": f"File {file.filename} fully ingested into WikiLLM system.",
                "status": "fully_processed",
                "vector_indexed": True,
                "wiki_pages_generated": len(wiki_pages),
                "chunks": num_indexed
            }

        return {
            "file_id": file_id,
            "filename": file.filename,
            "saved_path": str(saved_file_path),
            "size_bytes": size_bytes,
            "message": f"Uploaded {file.filename} successfully.",
            "status": "uploaded"
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=_traceback.format_exc())


@app.post("/documents/{file_id}/parse")
async def parse_document_endpoint(file_id: str):
    """Parse an uploaded document into text pages."""
    doc_record = DOCUMENT_STORE.get(file_id)
    if not doc_record:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        parsed = parse_document_bytes(doc_record["file_bytes"], doc_record["filename"])
        doc_record["parsed_data"] = parsed
        doc_record["status"] = "parsed"

        return {
            "file_id": file_id,
            "filename": doc_record["filename"],
            "total_pages": parsed["total_pages"],
            "pages": parsed["pages"],
            "full_text": parsed["full_text"],
            "status": "parsed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{file_id}/parsed")
async def get_parsed_document_endpoint(file_id: str):
    """Get stored parsed JSON output for document."""
    doc_record = DOCUMENT_STORE.get(file_id)
    if not doc_record or not doc_record.get("parsed_data"):
        raise HTTPException(status_code=404, detail="Parsed document data not found.")

    parsed = doc_record["parsed_data"]
    return {
        "file_id": file_id,
        "filename": doc_record["filename"],
        "total_pages": parsed["total_pages"],
        "pages": parsed["pages"],
        "full_text": parsed["full_text"],
        "status": "parsed"
    }


@app.post("/documents/{file_id}/generate-wiki")
async def generate_wiki_endpoint(file_id: str):
    """Generate Wiki Markdown pages from parsed document."""
    doc_record = DOCUMENT_STORE.get(file_id)
    if not doc_record:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        if not doc_record.get("parsed_data"):
            doc_record["parsed_data"] = parse_document_bytes(doc_record["file_bytes"], doc_record["filename"])

        cleaned = clean_text(doc_record["parsed_data"]["full_text"])
        doc_record["cleaned_text"] = cleaned

        wiki_pages = generate_wiki_pages_from_text(cleaned, doc_record["filename"], wiki_dir=str(WIKI_DIR))
        doc_record["wiki_pages"] = wiki_pages
        doc_record["status"] = "wiki_generated"

        return {
            "file_id": file_id,
            "status": "wiki_generated",
            "total_pages_generated": len(wiki_pages),
            "pages": [p["entity_name"] for p in wiki_pages]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/{file_id}/process-full-pipeline")
async def process_full_pipeline_endpoint(file_id: str):
    """Manually trigger complete 4-step WikiLLM ingestion pipeline."""
    doc_record = DOCUMENT_STORE.get(file_id)
    if not doc_record:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        parsed = parse_document_bytes(doc_record["file_bytes"], doc_record["filename"])
        doc_record["parsed_data"] = parsed

        cleaned = clean_text(parsed["full_text"])
        doc_record["cleaned_text"] = cleaned

        wiki_pages = generate_wiki_pages_from_text(cleaned, doc_record["filename"], wiki_dir=str(WIKI_DIR))
        doc_record["wiki_pages"] = wiki_pages

        num_indexed = index_wiki_documents(wiki_pages)
        doc_record["vector_indexed"] = True
        doc_record["status"] = "fully_processed"

        return {
            "file_id": file_id,
            "status": "fully_processed",
            "vector_indexed": True,
            "wiki_pages_generated": len(wiki_pages),
            "chunks": num_indexed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wiki/index")
async def get_wiki_index():
    """Return index catalog of generated Wiki pages."""
    index_file = WIKI_DIR / "index.json"
    if not index_file.exists():
        return {"total_pages": 0, "pages": []}

    try:
        return json.loads(index_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read wiki index: {str(e)}")


@app.get("/wiki/graph")
async def get_wiki_graph():
    """Return Knowledge Graph nodes and edges for visualization."""
    graph_file = WIKI_DIR / "graph.json"
    index_file = WIKI_DIR / "index.json"

    if graph_file.exists():
        try:
            return json.loads(graph_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    if index_file.exists():
        try:
            data = json.loads(index_file.read_text(encoding="utf-8"))
            if "graph" in data:
                return data["graph"]
        except Exception:
            pass

    return {"nodes": [], "edges": []}


@app.get("/wiki/page/{entity_name}")
async def get_wiki_page(entity_name: str):
    """Return content of specific Wiki Knowledge Markdown page."""
    normalized = entity_name.replace(" ", "_")
    md_path = WIKI_DIR / f"{normalized}.md"

    if not md_path.exists():
        matches = [f for f in WIKI_DIR.glob("*.md") if f.stem.lower() == normalized.lower()]
        if matches:
            md_path = matches[0]
        else:
            raise HTTPException(status_code=404, detail=f"Wiki page for '{entity_name}' not found.")

    content = md_path.read_text(encoding="utf-8")
    return {
        "entity_name": entity_name,
        "filename": md_path.name,
        "content": content
    }


@app.post("/qa", response_model=QAResponse)
@app.post("/qa/ask")
async def qa_endpoint(request: QuestionRequest):
    """Expose the multi-agent WikiLLM QA flow via POST /qa or POST /qa/ask."""
    try:
        result = await answer_question(request.question)
        answer_text = result.get("answer", "No answer generated.")
        context_text = result.get("context", "No context retrieved.")
        
        return {
            "answer": answer_text,
            "context": context_text,
            "grounded": "lack sufficient details" not in answer_text.lower()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index-pdf")
async def index_pdf_endpoint(file: UploadFile = File(...)):
    """PDF index endpoint wrapper utilizing full WikiLLM pipeline."""
    try:
        file_bytes = await file.read()
        num_indexed = index_documents_from_bytes(file_bytes, filename=file.filename)
        return {
            "message": f"Successfully indexed {file.filename} into WikiLLM system.",
            "chunks": num_indexed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=_traceback.format_exc())


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint for basic API info."""
    return {
        "name": "WikiLLM Intelligent Knowledge Management System",
        "version": "2.0.0",
        "endpoints": {
            "upload": "POST /upload",
            "qa": "POST /qa",
            "wiki_index": "GET /wiki/index",
            "health": "GET /health",
        },
    }