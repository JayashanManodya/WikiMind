"""Tools available to agents in the multi-agent WikiLLM system."""

from langchain_core.tools import tool

from ..retrieval.vector_store import retrieve
from ..retrieval.serialization import serialize_wikis


@tool(response_format="content_and_artifact")
def retrieval_tool(query: str, user_id: str = "guest_user"):
    """Search the vector database for relevant full Wiki Knowledge Markdown files.

    This tool retrieves complete Wiki Markdown document files from the Pinecone
    vector store based on the search query.

    Args:
        query: Search query string to locate relevant Wiki Knowledge pages.
        user_id: User ID for isolation.

    Returns:
        Tuple of (serialized_content, artifact) where:
        - serialized_content: Formatted string containing full Wiki Markdown files.
        - artifact: List of Document objects with full metadata.
    """
    # Retrieve full Wiki documents from vector store scoped to user
    docs = retrieve(query, k=3, user_id=user_id)

    # Serialize complete Wiki markdown pages into formatted string
    context = serialize_wikis(docs)

    return context, docs
