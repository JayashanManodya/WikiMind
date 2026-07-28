"""Vector store wrapper for Pinecone integration with LangChain in WikiLLM architecture, featuring Graph-Aware Wiki Retrieval."""

import io
import re
from pathlib import Path
from functools import lru_cache
from typing import List, Dict, Any

from pinecone import Pinecone
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings

from ..config import get_settings
from ..ingestion.parser import parse_document_bytes
from ..ingestion.cleaner import clean_text
from ..ingestion.wiki_generator import generate_wiki_pages_from_text


@lru_cache(maxsize=1)
def _get_vector_store() -> PineconeVectorStore | None:
    """Create a PineconeVectorStore instance configured from settings."""
    settings = get_settings()

    try:
        embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model_name,
            api_key=settings.openai_api_key,
        )

        return PineconeVectorStore(
            index_name=settings.pinecone_index_name,
            embedding=embeddings,
            pinecone_api_key=settings.pinecone_api_key
        )
    except Exception as e:
        print(f"Warning: Could not initialize Pinecone vector store ({e})")
        return None

def get_retriever(k: int | None = None):
    """Get a Pinecone retriever instance."""
    settings = get_settings()
    if k is None:
        k = settings.retrieval_k

    vector_store = _get_vector_store()
    if vector_store:
        return vector_store.as_retriever(search_kwargs={"k": k})
    return None


def retrieve(query: str, k: int | None = None, follow_relations: bool = True) -> List[Document]:
    """Retrieve full Wiki documents with 1-hop relationship graph traversal.

    Args:
        query: Search query string.
        k: Number of seed Wiki documents to retrieve.
        follow_relations: If True, automatically fetches 1-hop connected Wiki pages.

    Returns:
        List of Document objects representing seed and connected Wiki Markdown pages.
    """
    settings = get_settings()
    if k is None:
        k = settings.retrieval_k

    seed_docs: List[Document] = []
    try:
        vector_store = _get_vector_store()
        if vector_store:
            seed_docs = vector_store.similarity_search(query, k=k)
    except Exception as e:
        print(f"Warning: Vector DB retrieval failed ({e}). Falling back to local Wiki files.")

    wiki_dir = Path("wiki")
    if not seed_docs and wiki_dir.exists():
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        for md_file in wiki_dir.glob("*.md"):
            if md_file.name == "Index.md":
                continue
            content = md_file.read_text(encoding="utf-8")
            content_lower = content.lower()

            if any(term in content_lower for term in query_terms) or not query_terms:
                seed_docs.append(Document(
                    page_content=content,
                    metadata={"source": md_file.name, "entity_name": md_file.stem, "is_wiki": True}
                ))
            if len(seed_docs) >= k:
                break

    if not follow_relations or not seed_docs:
        return seed_docs

    # Graph Traversal: 1-hop relationship expansion
    retrieved_sources = {doc.metadata.get("source") for doc in seed_docs if doc.metadata.get("source")}
    retrieved_entities = {doc.metadata.get("entity_name") for doc in seed_docs if doc.metadata.get("entity_name")}

    connected_entity_names = set()
    for doc in seed_docs:
        matches = re.findall(r"\[\[(.*?)\]\]", doc.page_content)
        for m in matches:
            clean_name = m.strip()
            if clean_name and clean_name not in retrieved_entities:
                connected_entity_names.add(clean_name)

    connected_docs: List[Document] = []
    if wiki_dir.exists():
        for entity in connected_entity_names:
            normalized = entity.replace(" ", "_")
            md_file = wiki_dir / f"{normalized}.md"
            if not md_file.exists():
                matches = [f for f in wiki_dir.glob("*.md") if f.stem.lower() == normalized.lower()]
                if matches:
                    md_file = matches[0]

            if md_file.exists() and md_file.name not in retrieved_sources:
                content = md_file.read_text(encoding="utf-8")
                connected_docs.append(Document(
                    page_content=content,
                    metadata={"source": md_file.name, "entity_name": entity, "is_wiki": True, "is_graph_hop": True}
                ))
                retrieved_sources.add(md_file.name)

    return seed_docs + connected_docs


def index_wiki_documents(wiki_pages: List[Dict[str, Any]]) -> int:
    """Index full Wiki Markdown pages into the Pinecone vector store without 500-char chunking.

    Args:
        wiki_pages: List of dicts containing entity_name, filename, content, entity_type.

    Returns:
        The number of Wiki Markdown documents indexed.
    """
    docs = []
    for page in wiki_pages:
        doc = Document(
            page_content=page["content"],
            metadata={
                "source": page.get("filename", ""),
                "entity_name": page.get("entity_name", ""),
                "entity_type": page.get("entity_type", "CONCEPT"),
                "is_wiki": True
            }
        )
        docs.append(doc)

    if docs:
        try:
            vector_store = _get_vector_store()
            if vector_store:
                vector_store.add_documents(docs)
        except Exception as e:
            print(f"Note: Vector storage skipped or failed ({e}). Local Wiki Markdown files were saved.")

    return len(docs)


def index_documents_from_bytes(file_bytes: bytes, filename: str = "upload.pdf") -> int:
    """Run full WikiLLM pipeline from bytes: Parsing -> Cleaning -> Wiki Generation -> Vector Indexing.

    Args:
        file_bytes: Raw file content as bytes (PDF, DOCX, TXT, MD).
        filename: Original filename.

    Returns:
        The number of full Wiki Markdown documents indexed into Pinecone.
    """
    # Step 1: Parse
    parsed_doc = parse_document_bytes(file_bytes, filename)
    raw_text = parsed_doc["full_text"]

    # Step 2: Clean
    cleaned = clean_text(raw_text)

    # Step 3: Wiki Generation
    wiki_pages = generate_wiki_pages_from_text(cleaned, filename)

    # Step 4: Index full Wiki Markdown documents
    num_indexed = index_wiki_documents(wiki_pages)
    return num_indexed


def index_documents(file_path: Path) -> int:
    """Index a document file from disk using the full WikiLLM pipeline."""
    file_bytes = file_path.read_bytes()
    return index_documents_from_bytes(file_bytes, filename=file_path.name)