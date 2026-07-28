"""Utilities for serializing full Wiki Knowledge Markdown files into context strings for LLMs."""

from typing import List
from langchain_core.documents import Document

def serialize_wikis(docs: List[Document]) -> str:
    """Consolidate full Wiki Markdown documents into a formatted context string.

    Args:
        docs: List of Document objects representing full Wiki Markdown pages.

    Returns:
        Formatted Wiki Knowledge CONTEXT string.
    """
    if not docs:
        return "No relevant Wiki knowledge found."

    context_parts = []
    for i, doc in enumerate(docs, 1):
        entity = doc.metadata.get("entity_name") or doc.metadata.get("source", f"Wiki Page {i}")
        is_graph_hop = doc.metadata.get("is_graph_hop", False)
        hop_label = " (Connected via Knowledge Graph Link)" if is_graph_hop else " (Direct Semantic Match)"
        
        content = doc.page_content.strip()
        context_parts.append(f"=== Wiki Knowledge File {i}: {entity}{hop_label} ===\n{content}")

    return "\n\n" + ("=" * 50) + "\n\n" + "\n\n".join(context_parts)

# Alias for backwards compatibility
serialize_chunks = serialize_wikis
