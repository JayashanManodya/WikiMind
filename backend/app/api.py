"""FastAPI entry point for the WikiMind System with Google OAuth 2.0 and Per-User Data Isolation."""

import uuid
import json
import traceback as _traceback
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, File, UploadFile, Query, Depends, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models import QuestionRequest, QAResponse
from .services.qa_service import answer_question
from .core.ingestion.parser import parse_document_bytes
from .core.ingestion.wiki_generator import generate_wiki_pages_from_text, run_ingestion_pipeline
from .core.auth import get_current_user, verify_google_token, create_access_token
from .core.config import get_settings


def run_ingestion_in_background(
    file_bytes: bytes,
    filename: str,
    user_id: str,
    user_wiki_dir: str,
    doc_record: Dict[str, Any]
):
    """Background worker function for asynchronous 8-stage document ingestion pipeline."""
    try:
        pipeline_res = run_ingestion_pipeline(
            file_bytes=file_bytes,
            filename=filename,
            user_id=user_id,
            wiki_dir=user_wiki_dir
        )
        wiki_pages = pipeline_res.get("wiki_pages", [])
        doc_record["wiki_pages"] = wiki_pages
        doc_record["parsed_data"] = pipeline_res.get("parsed_output")
        doc_record["cleaned_text"] = pipeline_res.get("cleaned_output", {}).get("cleaned_markdown", "")
        doc_record["vector_indexed"] = True
        doc_record["pages_created"] = pipeline_res.get("pages_created", [])
        doc_record["pages_updated"] = pipeline_res.get("pages_updated", [])
        doc_record["status"] = "fully_processed"
        doc_record["message"] = f"File {filename} successfully processed into Knowledge Graph."
    except Exception as e:
        doc_record["status"] = "failed"
        doc_record["error"] = str(e)
        print(f"Background ingestion error for {filename}: {e}")


class GoogleAuthRequest(BaseModel):
    credential: str


app = FastAPI(
    title="WikiMind Intelligent Knowledge Management System",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS from settings
sys_settings = get_settings()
raw_origins = sys_settings.cors_origins.split(",") if sys_settings.cors_origins else ["*"]
allowed_origins = []
for o in raw_origins:
    s = o.strip()
    if s:
        allowed_origins.append(s)
        if s != "*" and s.endswith("/"):
            allowed_origins.append(s.rstrip("/"))
        elif s != "*" and not s.endswith("/"):
            allowed_origins.append(s + "/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .core.paths import get_user_wiki_dir, get_user_raw_docs_dir
from .core.graph_db import (
    init_neo4j_schema,
    upsert_user_node,
    get_user_wiki_pages,
    get_wiki_page_by_title,
    delete_wiki_page,
    get_user_knowledge_graph,
    get_user_chat_sessions,
    get_chat_history,
    delete_chat_session,
    save_chat_message,
    create_chat_session
)

# Per-User document storage store (user_id -> file_id -> dict)
DOCUMENT_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {}


@app.on_event("startup")
async def on_startup():
    """Initialize Neo4j database schema constraints & Lucene BM25 indexes on startup."""
    try:
        init_neo4j_schema()
    except Exception as e:
        print(f"Neo4j startup schema note: {e}")


@app.post("/auth/google")
async def google_login(payload: GoogleAuthRequest):
    """Authenticate or sign in with Google OAuth 2.0 ID Token / Credential."""
    try:
        user_data = await verify_google_token(payload.credential)
        token = create_access_token(user_data)
        
        # Upsert user node in Neo4j
        try:
            upsert_user_node(
                user_id=user_data.get("user_id", "guest"),
                email=user_data.get("email", ""),
                name=user_data.get("name", ""),
                picture=user_data.get("picture", "")
            )
        except Exception as ex:
            print(f"Neo4j upsert user note: {ex}")

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user_data
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")



@app.get("/auth/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return currently authenticated user session details."""
    return current_user


@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_process: bool = Query(True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload PDF, DOCX, HTML, Markdown, Image, or PPTX document and run 8-stage WikiLLM ingestion pipeline asynchronously."""
    user_id = current_user["user_id"]
    allowed_exts = [".pdf", ".docx", ".doc", ".html", ".htm", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp", ".pptx", ".ppt"]
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

        saved_file_path = f"in_memory://{user_id}/{file_id}_{file.filename}"


        doc_record = {
            "file_id": file_id,
            "user_id": user_id,
            "filename": file.filename,
            "saved_path": str(saved_file_path),
            "size_bytes": size_bytes,
            "file_bytes": file_bytes,
            "status": "processing" if auto_process else "uploaded",
            "parsed_data": None,
            "cleaned_text": None,
            "wiki_pages": [],
            "vector_indexed": False
        }
        
        if user_id not in DOCUMENT_STORE:
            DOCUMENT_STORE[user_id] = {}
        DOCUMENT_STORE[user_id][file_id] = doc_record

        user_wiki_dir = get_user_wiki_dir(user_id)

        if auto_process:
            # Dispatch background task for non-blocking 8-stage pipeline ingestion
            background_tasks.add_task(
                run_ingestion_in_background,
                file_bytes,
                file.filename,
                user_id,
                str(user_wiki_dir),
                doc_record
            )

            return {
                "file_id": file_id,
                "filename": file.filename,
                "saved_path": str(saved_file_path),
                "size_bytes": size_bytes,
                "message": f"File '{file.filename}' uploaded successfully. Pipeline is processing in the background.",
                "status": "processing",
                "vector_indexed": False,
                "pages_created": [],
                "pages_updated": [],
                "wiki_pages_generated": 0
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


@app.get("/documents/{file_id}/status")
async def get_document_status(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieve processing status of an uploaded document task."""
    user_id = current_user["user_id"]
    doc_record = DOCUMENT_STORE.get(user_id, {}).get(file_id)
    if not doc_record:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {
        "file_id": file_id,
        "filename": doc_record["filename"],
        "status": doc_record.get("status", "uploaded"),
        "message": doc_record.get("message", ""),
        "pages_created": doc_record.get("pages_created", []),
        "pages_updated": doc_record.get("pages_updated", []),
        "wiki_pages_generated": len(doc_record.get("wiki_pages", [])),
        "error": doc_record.get("error")
    }



@app.post("/documents/{file_id}/parse")
async def parse_document_endpoint(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Parse an uploaded document into text pages."""
    user_id = current_user["user_id"]
    doc_record = DOCUMENT_STORE.get(user_id, {}).get(file_id)
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
async def get_parsed_document_endpoint(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get stored parsed JSON output for document."""
    user_id = current_user["user_id"]
    doc_record = DOCUMENT_STORE.get(user_id, {}).get(file_id)
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
async def generate_wiki_endpoint(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Generate Wiki Markdown pages from parsed document."""
    user_id = current_user["user_id"]
    doc_record = DOCUMENT_STORE.get(user_id, {}).get(file_id)
    if not doc_record:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        if not doc_record.get("parsed_data"):
            doc_record["parsed_data"] = parse_document_bytes(doc_record["file_bytes"], doc_record["filename"])

        raw_text = doc_record["parsed_data"]["full_text"]
        doc_record["cleaned_text"] = raw_text

        user_wiki_dir = get_user_wiki_dir(user_id)
        wiki_pages = generate_wiki_pages_from_text(raw_text, doc_record["filename"], wiki_dir=str(user_wiki_dir))
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
async def process_full_pipeline_endpoint(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Manually trigger complete 4-step WikiLLM ingestion pipeline."""
    user_id = current_user["user_id"]
    doc_record = DOCUMENT_STORE.get(user_id, {}).get(file_id)
    if not doc_record:
        for uid, docs in DOCUMENT_STORE.items():
            if isinstance(docs, dict) and file_id in docs:
                doc_record = docs[file_id]
                break
    if not doc_record:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        file_bytes = doc_record.get("file_bytes")
        if not file_bytes and doc_record.get("saved_path") and Path(doc_record["saved_path"]).exists():
            file_bytes = Path(doc_record["saved_path"]).read_bytes()
        user_wiki_dir = get_user_wiki_dir(user_id)
        pipeline_res = run_ingestion_pipeline(
            file_bytes=file_bytes,
            filename=doc_record["filename"],
            user_id=user_id,
            wiki_dir=str(user_wiki_dir)
        )
        wiki_pages = pipeline_res.get("wiki_pages", [])
        doc_record["wiki_pages"] = wiki_pages
        doc_record["parsed_data"] = pipeline_res.get("parsed_output")
        doc_record["cleaned_text"] = pipeline_res.get("cleaned_output", {}).get("cleaned_markdown", "")
        doc_record["status"] = "fully_processed"

        return {
            "file_id": file_id,
            "status": "fully_processed",
            "graph_indexed": True,
            "wiki_pages_generated": len(wiki_pages),
            "chunks": len(wiki_pages)
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wiki/index")
async def get_wiki_index(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return cumulative index catalog of all generated Wiki pages for the current user from Neo4j."""
    user_id = current_user["user_id"]
    db_pages = get_user_wiki_pages(user_id)

    if db_pages:
        pages = []
        for p in db_pages:
            pages.append({
                "entity_name": p["title"],
                "filename": p.get("file_name", f"{p['title']}.md"),
                "entity_type": p.get("category", "General"),
                "summary": p.get("summary", ""),
                "related_entities": p.get("links", [])
            })
        return {
            "total_pages": len(pages),
            "pages": pages
        }

    # Fallback to filesystem index.json if Neo4j graph is empty
    user_wiki_dir = get_user_wiki_dir(user_id)
    index_file = user_wiki_dir / "index.json"
    if not index_file.exists():
        root_index = Path("wiki/index.json")
        if root_index.exists():
            index_file = root_index
        else:
            return {"total_pages": 0, "pages": []}

    try:
        return json.loads(index_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read wiki index: {str(e)}")


@app.get("/wiki/graph")
async def get_wiki_graph(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return cumulative Knowledge Graph nodes and edges for visual interactive canvas for current user."""
    user_id = current_user["user_id"]
    graph_data = get_user_knowledge_graph(user_id)

    if graph_data["nodes"]:
        return {
            "nodes": [
                {
                    "id": n["id"],
                    "label": n["name"],
                    "type": n["category"],
                    "summary": n.get("summary", "")
                }
                for n in graph_data["nodes"]
            ],
            "edges": [
                {
                    "source": l["source"],
                    "relation": l["type"],
                    "target": l["target"]
                }
                for l in graph_data["links"]
            ]
        }

    # Fallback to filesystem graph.json if database is empty
    user_wiki_dir = get_user_wiki_dir(user_id)
    graph_file = user_wiki_dir / "graph.json"
    if graph_file.exists():
        try:
            return json.loads(graph_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {"nodes": [], "edges": []}


@app.get("/wiki/page/{entity_name}")
async def get_wiki_page(
    entity_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Return content of specific Wiki Knowledge Markdown page for the current user from Neo4j."""
    user_id = current_user["user_id"]

    # Try Neo4j graph database first
    db_rec = get_wiki_page_by_title(user_id, entity_name)
    if not db_rec:
        db_rec = get_wiki_page_by_title(user_id, entity_name.replace(" ", "_"))

    if db_rec:
        return {
            "entity_name": db_rec["title"],
            "filename": db_rec.get("file_name", f"{db_rec['title']}.md"),
            "content": db_rec["content"]
        }

    # File system fallback
    user_wiki_dir = get_user_wiki_dir(user_id)
    normalized = entity_name.replace(" ", "_")
    md_path = user_wiki_dir / f"{normalized}.md"

    if not md_path.exists():
        matches = [f for f in user_wiki_dir.glob("*.md") if f.stem.lower() == normalized.lower()]
        if matches:
            md_path = matches[0]
        else:
            root_dir = Path("wiki")
            root_matches = [f for f in root_dir.glob("*.md") if f.stem.lower() == normalized.lower()]
            if root_matches:
                md_path = root_matches[0]
            else:
                raise HTTPException(status_code=404, detail=f"Wiki page for '{entity_name}' not found.")

    content = md_path.read_text(encoding="utf-8")
    return {
        "entity_name": entity_name,
        "filename": md_path.name,
        "content": content
    }


@app.get("/api/chat/sessions")
async def get_chat_sessions_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve all saved chat sessions for current authenticated user from Neo4j."""
    user_id = current_user["user_id"]
    sessions = get_user_chat_sessions(user_id)
    return {"sessions": sessions}


@app.get("/api/chat/sessions/{session_id}/messages")
async def get_session_messages_endpoint(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieve message history for a specific chat session from Neo4j."""
    user_id = current_user["user_id"]
    messages = get_chat_history(user_id, session_id)
    return {"session_id": session_id, "messages": messages}


@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session_endpoint(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a chat session and all its messages in Neo4j."""
    user_id = current_user["user_id"]
    success = delete_chat_session(user_id, session_id)
    return {"status": "deleted", "session_id": session_id, "success": success}



@app.post("/qa", response_model=QAResponse)
@app.post("/qa/ask")
async def qa_endpoint(
    request: QuestionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Expose the multi-agent WikiLLM QA flow via POST /qa or POST /qa/ask (Scoped to current user)."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question string cannot be empty.")

    user_id = current_user["user_id"]
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Ensure session exists & save user question to Neo4j
        create_chat_session(user_id=user_id, session_id=session_id, title=request.question[:40])
        save_chat_message(
            user_id=user_id,
            session_id=session_id,
            role="user",
            content=request.question
        )

        result = await answer_question(request.question, user_id=user_id, history=request.history)
        answer_text = result.get("answer", "No answer generated.")
        context_text = result.get("context", "No context retrieved.")

        # Extract cited sources
        sources = []
        if context_text and context_text != "No context retrieved.":
            sources = [{"snippet": context_text[:300]}]

        # Save assistant response to Neo4j
        save_chat_message(
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            content=answer_text,
            citations=json.dumps(sources)
        )


        is_grounded = "lack sufficient details" not in answer_text.lower() and "does not contain" not in answer_text.lower() and "cannot answer" not in answer_text.lower()

        return {
            "question": request.question,
            "answer": answer_text,
            "context": context_text,
            "citations": ["wiki_page.md"] if is_grounded else [],
            "grounded": is_grounded
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/index-pdf")
async def index_pdf_endpoint(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """PDF index endpoint wrapper utilizing full WikiLLM Knowledge Graph pipeline."""
    user_id = current_user["user_id"]
    try:
        file_bytes = await file.read()
        user_wiki_dir = get_user_wiki_dir(user_id)
        pipeline_res = run_ingestion_pipeline(
            file_bytes=file_bytes,
            filename=file.filename,
            user_id=user_id,
            wiki_dir=str(user_wiki_dir)
        )
        return {
            "message": f"Successfully ingested {file.filename} into WikiLLM Knowledge Graph system.",
            "pages_generated": len(pipeline_res.get("wiki_pages", []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=_traceback.format_exc())



class DebugWikiRequest(BaseModel):
    text: str
    filename: Optional[str] = "debug_document.txt"


@app.post("/debug/parse")
async def debug_parse_endpoint(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Standalone debug endpoint to test Document Parser individually."""
    try:
        file_bytes = await file.read()
        parsed = parse_document_bytes(file_bytes, file.filename)
        return {
            "filename": file.filename,
            "total_pages": parsed["total_pages"],
            "character_count": len(parsed["full_text"]),
            "pages": parsed["pages"],
            "full_text": parsed["full_text"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/debug/generate-wiki")
async def debug_generate_wiki_endpoint(
    request: DebugWikiRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Standalone debug endpoint to test Wiki Generator individually."""
    try:
        user_id = current_user["user_id"]
        user_wiki_dir = get_user_wiki_dir(user_id)
        pages = generate_wiki_pages_from_text(request.text, request.filename, wiki_dir=str(user_wiki_dir))
        return {
            "filename": request.filename,
            "user_id": user_id,
            "total_pages_generated": len(pages),
            "pages": pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint for basic API info."""
    return {
        "name": "WikiMind Intelligent Knowledge Management System",
        "version": "2.0.0",
        "endpoints": {
            "auth_google": "POST /auth/google",
            "auth_me": "GET /auth/me",
            "upload": "POST /upload",
            "qa": "POST /qa",
            "wiki_index": "GET /wiki/index",
            "health": "GET /health",
        },
    }