from fastapi import APIRouter, HTTPException, status
from BackEnd.schemas import (
    RetrievalRequest,
    RetrievalContextResponse,
    ErrorDetail
)
from BackEnd.services.retriever_service import retriever_service

router = APIRouter(prefix="/retrieval", tags=["Intelligent Retrieval Engine"])

@router.post(
    "/context",
    response_model=RetrievalContextResponse,
    summary="Retrieve Multi-Hop Knowledge Context",
    description="Executes Hop-1 vector similarity retrieval, Hop-2 graph connection expansion over wiki links, and assembles character-budgeted context for LLM question answering.",
    responses={
        400: {"model": ErrorDetail, "description": "Invalid retrieval request"}
    }
)
def retrieve_context(request: RetrievalRequest):
    """Trigger multi-hop knowledge context retrieval for user question"""
    return retriever_service.retrieve_multi_hop_context(
        question=request.question,
        top_k=request.top_k,
        max_chars=request.max_chars
    )
