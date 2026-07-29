"""Vector store wrapper for Pinecone integration with LangChain in WikiLLM architecture, featuring Graph-Aware Wiki Retrieval."""

import io
import re
from pathlib import Path
from functools import lru_cache
from typing import List, Dict, Any

try:
    from pinecone import Pinecone
    from langchain_pinecone import PineconeVectorStore
except ImportError:
    Pinecone = None
    PineconeVectorStore = None

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

from ..config import get_settings
from ..paths import get_user_wiki_dir
from ..ingestion.parser import parse_document_bytes
from ..ingestion.wiki_generator import generate_wiki_pages_from_text

# Global per-user in-memory vector store registry for fallback storage
USER_VECTOR_STORES: Dict[str, InMemoryVectorStore] = {}


def _get_vector_store(user_id: str = "default_user") -> Any:
    """Get PineconeVectorStore if configured, or fall back to a per-user InMemoryVectorStore."""
    settings = get_settings()

    try:
        embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model_name,
            api_key=settings.openai_api_key,
        )
    except Exception as e:
        print(f"Warning: Embeddings initialization failed ({e})")
        return None

    # Try Pinecone vector store if Pinecone library and API key are available
    if PineconeVectorStore and settings.pinecone_api_key and not settings.pinecone_api_key.startswith("pcsk_placeholder"):
        try:
            return PineconeVectorStore(
                index_name=settings.pinecone_index_name,
                embedding=embeddings,
                pinecone_api_key=settings.pinecone_api_key
            )
        except Exception as e:
            print(f"Note: Pinecone initialization failed ({e}). Falling back to local VectorStore.")

    # Fallback: Per-user InMemoryVectorStore (guarantees 100% vector embedding capability)
    if user_id not in USER_VECTOR_STORES:
        USER_VECTOR_STORES[user_id] = InMemoryVectorStore(embeddings)

    return USER_VECTOR_STORES[user_id]


def get_retriever(k: int | None = None, user_id: str = "default_user"):
    """Get a vector retriever instance for the specified user."""
    settings = get_settings()
    if k is None:
        k = settings.retrieval_k

    vector_store = _get_vector_store(user_id)
    if vector_store:
        return vector_store.as_retriever(search_kwargs={"k": k})
    return None


def retrieve(query: str, k: int | None = None, follow_relations: bool = True, user_id: str = "default_user") -> List[Document]:
    """Retrieve full Wiki documents with 1-hop relationship graph traversal scoped to user.

    Args:
        query: Search query string.
        k: Number of seed Wiki documents to retrieve.
        follow_relations: If True, automatically fetches 1-hop connected Wiki pages.
        user_id: User identifier to scope search results.

    Returns:
        List of Document objects representing seed and connected Wiki Markdown pages.
    """
    settings = get_settings()
    if k is None:
        k = settings.retrieval_k

    seed_docs: List[Document] = []
    try:
        vector_store = _get_vector_store(user_id)
        if vector_store:
            filter_dict = {"user_id": {"$eq": user_id}}
            try:
                seed_docs = vector_store.similarity_search(query, k=k, filter=filter_dict, namespace=user_id)
            except Exception:
                try:
                    seed_docs = vector_store.similarity_search(query, k=k, filter=filter_dict)
                except Exception:
                    seed_docs = vector_store.similarity_search(query, k=k)
    except Exception as e:
        print(f"Warning: Vector DB retrieval error ({e}). Falling back to local user Wiki files.")

    from ..db import get_user_wiki_pages_db, get_wiki_page_db

    if not seed_docs:
        db_pages = get_user_wiki_pages_db(user_id)
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        for p in db_pages:
            content = p["content_md"]
            content_lower = content.lower()

            if any(term in content_lower for term in query_terms) or not query_terms:
                seed_docs.append(Document(
                    page_content=content,
                    metadata={"source": p["filename"], "entity_name": p["entity_name"], "is_wiki": True, "user_id": user_id}
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
    for entity in connected_entity_names:
        db_rec = get_wiki_page_db(user_id, entity)
        if db_rec and db_rec.get("filename") not in retrieved_sources:
            connected_docs.append(Document(
                page_content=db_rec["content_md"],
                metadata={"source": db_rec["filename"], "entity_name": entity, "is_wiki": True, "is_graph_hop": True, "user_id": user_id}
            ))
            retrieved_sources.add(db_rec["filename"])

    return seed_docs + connected_docs


def index_wiki_documents(wiki_pages: List[Dict[str, Any]], user_id: str = "default_user") -> int:
    """Index full Wiki Markdown pages into the active vector store with user isolation metadata.

    Args:
        wiki_pages: List of dicts containing entity_name, filename, content, entity_type.
        user_id: User identifier.

    Returns:
        The number of Wiki Markdown documents indexed into vector store.
    """
    docs = []
    for page in wiki_pages:
        doc = Document(
            page_content=page["content"],
            metadata={
                "source": page.get("filename", ""),
                "entity_name": page.get("entity_name", ""),
                "entity_type": page.get("entity_type", "CONCEPT"),
                "is_wiki": True,
                "user_id": user_id
            }
        )
        docs.append(doc)

    if docs:
        try:
            vector_store = _get_vector_store(user_id)
            if vector_store:
                try:
                    vector_store.add_documents(docs, namespace=user_id)
                except Exception:
                    vector_store.add_documents(docs)
                print(f"Successfully embedded {len(docs)} Wiki pages into vector database for user {user_id}.")
        except Exception as e:
            print(f"Note: Vector storage embedding failed ({e}). Local Wiki Markdown files were saved.")

    return len(docs)


def index_documents_from_bytes(file_bytes: bytes, filename: str = "upload.pdf", user_id: str = "guest_user") -> int:
    """Run full WikiLLM pipeline from bytes: Parsing -> Cleaning -> Wiki Generation -> Vector Indexing.

    Args:
        file_bytes: Raw file content as bytes (PDF, DOCX, TXT, MD).
        filename: Original filename.
        user_id: User identifier for isolation.

    Returns:
        The number of full Wiki Markdown documents indexed into Pinecone.
    """
    # Step 1: Parse
    parsed_doc = parse_document_bytes(file_bytes, filename)
    raw_text = parsed_doc["full_text"]

    # Step 2: Wiki Generation (scoped to user's wiki directory using raw text directly)
    user_wiki_dir = f"wiki/users/{user_id}"
    wiki_pages = generate_wiki_pages_from_text(raw_text, filename, wiki_dir=user_wiki_dir)

    # Step 3: Index full Wiki Markdown documents with user_id
    num_indexed = index_wiki_documents(wiki_pages, user_id=user_id)
    return num_indexed


def index_documents(file_path: Path, user_id: str = "guest_user") -> int:
    """Index a document file from disk using the full WikiLLM pipeline."""
    file_bytes = file_path.read_bytes()
    return index_documents_from_bytes(file_bytes, filename=file_path.name, user_id=user_id)