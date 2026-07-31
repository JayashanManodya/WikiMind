"""LangGraph orchestration for the linear multi-agent QA flow."""

from functools import lru_cache
from typing import Any, Dict

from langgraph.constants import END, START
from langgraph.graph import StateGraph

from .agents import grounded_qa_node
from .state import QAState


def create_qa_graph() -> Any:
    """Create and compile the optimized direct grounded QA graph.

    The graph executes in order:
    1. Grounded QA Agent: performs direct vector retrieval and single-pass grounded answer synthesis.

    Returns:
        Compiled graph ready for execution.
    """
    builder = StateGraph(QAState)

    # Add node for grounded QA agent
    builder.add_node("grounded_qa", grounded_qa_node)

    # Define linear flow: START -> grounded_qa -> END
    builder.add_edge(START, "grounded_qa")
    builder.add_edge("grounded_qa", END)

    return builder.compile()


@lru_cache(maxsize=1)
def get_qa_graph() -> Any:
    """Get the compiled QA graph instance (singleton via LRU cache)."""
    return create_qa_graph()


async def run_qa_flow(
    question: str, 
    user_id: str = "guest_user",
    history: list[dict] | None = None
) -> Dict[str, Any]:
    """Run the complete multi-agent QA flow for a question.

    Args:
        question: The user's question.
        user_id: The ID of the authenticated user.
        history: Complete conversation history list.

    Returns:
        Dictionary with final answer, context, and state metadata.
    """
    graph = get_qa_graph()

    initial_state: QAState = {
        "question": question,
        "context": None,
        "draft_answer": None,
        "answer": None,
        "user_id": user_id,
        "history": history or [],
        "messages": [],
    }

    final_state = await graph.ainvoke(initial_state)

    return final_state

