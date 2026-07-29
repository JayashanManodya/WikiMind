"""Service layer for handling QA requests.

This module provides a simple interface for the FastAPI layer to interact
with the multi-agent RAG pipeline without depending directly on LangGraph
or agent implementation details.
"""

from typing import Dict, Any

from ..core.agents.graph import run_qa_flow


async def answer_question(
    question: str, 
    user_id: str = "guest_user",
    history: list[dict] | None = None
) -> Dict[str, Any]:
    """Run the multi-agent QA flow for a given question, user context, and conversation history.

    Args:
        question: User's natural language question.
        user_id: User ID for document isolation.
        history: Optional list of previous chat messages.

    Returns:
        Dictionary containing at least `answer` and `context` keys.
    """
    return await run_qa_flow(question, user_id=user_id, history=history)
