"""LangGraph orchestration for the linear multi-agent QA flow."""

from functools import lru_cache
from typing import Any, Dict

from langgraph.constants import END, START
from langgraph.graph import StateGraph

from .agents import retrieval_node, summarization_node, verification_node , planning_node
from .state import QAState


def create_qa_graph() -> Any:
    """Create and compile the linear multi-agent QA graph.

    The graph executes in order:
    1. Retrieval Agent: gathers context from vector store
    2. Summarization Agent: generates draft answer from context
    3. Verification Agent: verifies and corrects the answer

    Returns:
        Compiled graph ready for execution.
    """
    builder = StateGraph(QAState)

    # Add nodes for each agent
    builder.add_node("planning", planning_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("summarization", summarization_node)
    builder.add_node("verification", verification_node)

    # Define linear flow: START -> retrieval -> summarization -> verification -> END
    builder.add_edge(START, "planning")
    builder.add_edge("planning", "retrieval")
    builder.add_edge("retrieval", "summarization")
    builder.add_edge("summarization", "verification")
    builder.add_edge("verification", END)

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
        "plan": None,
        "sub_questions": None,
        "user_id": user_id,
        "history": history or [],
        "messages": [],
    }

    final_state = await graph.ainvoke(initial_state)

    return final_state

