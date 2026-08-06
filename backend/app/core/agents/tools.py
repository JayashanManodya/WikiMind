"""Tools available to agents in the multi-agent WikiLLM system."""

from langchain_core.tools import tool
from langchain_core.documents import Document

from ..graph_db import search_wiki_graph


@tool(response_format="content_and_artifact")
def retrieval_tool(query: str, user_id: str = "guest_user"):
    """Search the Neo4j Knowledge Graph for relevant Wiki Pages using BM25 and graph link traversal.

    Args:
        query: Search query string to locate relevant Wiki Knowledge pages.
        user_id: User ID for document isolation.

    Returns:
        Tuple of (serialized_content, artifact) containing retrieved Wiki pages.
    """
    # 1. Retrieve graph-connected wiki pages from Neo4j scoped to user_id
    graph_results = search_wiki_graph(user_id=user_id, search_query=query, limit=4)
    
    docs = []
    context_blocks = []

    for item in graph_results:
        title = item.get("title", "Untitled")
        content = item.get("content", "")
        summary = item.get("summary", "")
        category = item.get("category", "General")
        
        doc = Document(
            page_content=content if content else summary,
            metadata={"title": title, "category": category, "summary": summary}
        )
        docs.append(doc)
        context_blocks.append(f"### [[{title}]] (Category: {category})\n{content if content else summary}")

    serialized_content = "\n\n".join(context_blocks) if context_blocks else "No relevant Wiki pages found in Knowledge Graph."
    return serialized_content, docs

