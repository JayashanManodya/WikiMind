from fastapi import APIRouter, HTTPException, status
from BackEnd.schemas import (
    QARequest,
    QAResponse,
    ErrorDetail
)
from BackEnd.services.qa_service import qa_service

router = APIRouter(prefix="/qa", tags=["Grounded Question Answering Engine"])

@router.post(
    "/ask",
    response_model=QAResponse,
    summary="Ask Question (Grounded Wiki QA)",
    description="Retrieves multi-hop wiki context, injects strict grounding constraints, and generates factual answers with source citations. Refuses to answer if knowledge is absent.",
    responses={
        400: {"model": ErrorDetail, "description": "Invalid QA request"}
    }
)
def ask_question(request: QARequest):
    """Trigger Grounded Question Answering for user question"""
    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question string cannot be empty."
        )
    return qa_service.answer_question(
        question=request.question,
        top_k=request.top_k,
        max_chars=request.max_chars
    )
