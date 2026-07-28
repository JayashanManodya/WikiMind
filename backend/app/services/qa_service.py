"""Service layer for handling QA requests.

This module provides a simple interface for the FastAPI layer to interact
with the multi-agent RAG pipeline without depending directly on LangGraph
or agent implementation details.
"""

from typing import Dict, Any

from ..core.agents.graph import run_qa_flow


async def answer_question(question: str) -> Dict[str, Any]:
    """Run the multi-agent QA flow for a given question.

    Args:
        question: User's natural language question about the vector databases paper.

    Returns:
        Dictionary containing at least `answer` and `context` keys.
    """
    return await run_qa_flow(question)
