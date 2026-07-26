from fastapi import APIRouter, HTTPException, Query, status
from BackEnd.schemas import (
    SemanticSearchResponse,
    VectorIndexResponse,
    ErrorDetail
)
from BackEnd.services.vector_service import vector_service

router = APIRouter(prefix="/search", tags=["Semantic Vector Search Engine"])

@router.post(
    "/index-wiki",
    response_model=VectorIndexResponse,
    summary="Index All Wiki Pages for Vector Search",
    description="Scans generated wiki markdown files and generates persistent vector embeddings for semantic search.",
)
def index_all_wiki_pages():
    """Trigger vector embedding generation for all generated wiki pages"""
    return vector_service.index_all_wiki_pages()

@router.get(
    "/semantic",
    response_model=SemanticSearchResponse,
    summary="Perform Semantic Vector Search",
    description="Searches wiki knowledge base using vector similarity embeddings matching user concepts by meaning.",
    responses={
        400: {"model": ErrorDetail, "description": "Invalid search query"}
    }
)
def semantic_search(
    query: str = Query(..., description="Semantic search prompt or question (e.g., 'EV manufacturers', 'Tesla founder', 'Battery technology')"),
    top_k: int = Query(5, ge=1, le=20, description="Maximum number of top matching wiki pages to return")
):
    """Execute semantic vector similarity search"""
    if not query or len(query.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query string cannot be empty."
        )
    return vector_service.semantic_search(query=query, top_k=top_k)
