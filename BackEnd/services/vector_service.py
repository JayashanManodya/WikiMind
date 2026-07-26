import os
import re
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status

from BackEnd.schemas import (
    SemanticSearchResult,
    SemanticSearchResponse,
    VectorIndexResponse
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VECTORS_DIR = BACKEND_DIR / "storage" / "vectors"

class VectorService:
    def __init__(self, vectors_dir: Optional[Path] = None):
        self.vectors_dir = vectors_dir or DEFAULT_VECTORS_DIR
        self.vectors_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.vectors_dir / "index_vectors.json"
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # --- Cosine Similarity Helper ---

    def compute_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Computes Cosine Similarity score between two vector lists"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))

    # --- Embedding Generators ---

    def generate_embedding_openai(self, text: str) -> List[float]:
        """Call OpenAI Embeddings API for text-embedding-3-small"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            res = client.embeddings.create(
                model=self.model,
                input=text[:8000]
            )
            return res.data[0].embedding
        except Exception:
            return self.generate_embedding_deterministic(text)

    def generate_embedding_deterministic(self, text: str, dim: int = 128) -> List[float]:
        """
        Deterministic, offline NLP embedding generator.
        Constructs a normalized term-frequency and character n-gram feature vector representation.
        """
        if not text:
            return [0.0] * dim

        clean_text = text.lower()
        words = re.findall(r'\b[a-z0-9_\-]+\b', clean_text)
        
        vector = [0.0] * dim
        for w in words:
            # Hash word into vector dimensions using stable rolling polynomial hash
            word_hash = sum(ord(c) * (31 ** idx) for idx, c in enumerate(w))
            idx1 = word_hash % dim
            idx2 = (word_hash * 37) % dim
            vector[idx1] += 1.0
            vector[idx2] += 0.5

        # Character bi-gram features
        for i in range(len(clean_text) - 1):
            bigram_hash = ord(clean_text[i]) * 31 + ord(clean_text[i+1])
            idx = bigram_hash % dim
            vector[idx] += 0.1

        # L2 Normalize Vector
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def get_text_embedding(self, text: str) -> List[float]:
        """Generate embedding vector using OpenAI API if configured, else deterministic engine"""
        if self.api_key:
            return self.generate_embedding_openai(text)
        else:
            return self.generate_embedding_deterministic(text)

    # --- Vector Indexing Operations ---

    def load_vector_index(self) -> Dict[str, Any]:
        """Load vector index JSON file from storage/vectors/index_vectors.json"""
        if not self.index_file.exists():
            return {"total_pages": 0, "vectors": {}}
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"total_pages": 0, "vectors": {}}

    def save_vector_index(self, index_data: Dict[str, Any]):
        """Persist vector index JSON to storage/vectors/index_vectors.json"""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)

    def index_wiki_page(
        self,
        entity_name: str,
        filename: str,
        content: str,
        entity_type: str = "CONCEPT"
    ):
        """Generates embedding for a single wiki page and updates the vector store"""
        index_data = self.load_vector_index()
        vectors_dict = index_data.get("vectors", {})

        # Extract links from content
        links = list(set(re.findall(r'\[\[(.*?)\]\]', content)))

        # Create rich text payload for vector embedding
        text_to_embed = f"Title: {entity_name} | Type: {entity_type}\n{content}"
        vector = self.get_text_embedding(text_to_embed)

        # Snippet generation
        lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
        snippet = " ".join(lines[:3])[:250] if lines else f"Wiki page for {entity_name}."

        vectors_dict[entity_name] = {
            "entity_name": entity_name,
            "filename": filename,
            "entity_type": entity_type,
            "snippet": snippet,
            "links_to": links,
            "vector": vector
        }

        index_data["total_pages"] = len(vectors_dict)
        index_data["vector_dim"] = len(vector)
        index_data["vectors"] = vectors_dict
        self.save_vector_index(index_data)

    def index_all_wiki_pages(self) -> VectorIndexResponse:
        """Scans ./storage/wiki/ directory and embeds all markdown wiki pages into the vector database"""
        wiki_dir = BACKEND_DIR / "storage" / "wiki"
        if not wiki_dir.exists():
            return VectorIndexResponse(
                indexed_pages_count=0,
                vector_dim=128,
                status="indexed",
                message="No wiki directory found to index."
            )

        wiki_files = [p for p in wiki_dir.glob("*.md") if p.name not in ("Index.md", "README.md")]
        indexed_count = 0
        dim = 128

        for filepath in wiki_files:
            entity_name = filepath.stem.replace("_", " ")
            content = filepath.read_text(encoding="utf-8")
            
            type_match = re.search(r'\*\*Entity Type\*\*:\s*`([^`]+)`', content)
            entity_type = type_match.group(1) if type_match else "CONCEPT"

            self.index_wiki_page(entity_name, filepath.name, content, entity_type)
            indexed_count += 1

        index_data = self.load_vector_index()
        dim = index_data.get("vector_dim", 128)

        return VectorIndexResponse(
            indexed_pages_count=indexed_count,
            vector_dim=dim,
            status="indexed",
            message=f"Successfully generated vector embeddings for {indexed_count} wiki pages."
        )

    # --- Semantic Search Operations ---

    def semantic_search(self, query: str, top_k: int = 5) -> SemanticSearchResponse:
        """
        Generates query embedding vector, calculates Cosine Similarity across all stored
        wiki page vectors, and returns top_k ranked semantic search matches.
        """
        query_str = query.strip()
        if not query_str:
            return SemanticSearchResponse(query=query, total_results=0, results=[])

        index_data = self.load_vector_index()
        vectors_dict = index_data.get("vectors", {})

        # If vector index is empty, auto index existing wiki pages
        if not vectors_dict:
            self.index_all_wiki_pages()
            index_data = self.load_vector_index()
            vectors_dict = index_data.get("vectors", {})

        if not vectors_dict:
            return SemanticSearchResponse(query=query_str, total_results=0, results=[])

        query_vector = self.get_text_embedding(query_str)
        scored_results: List[Tuple[float, Dict[str, Any]]] = []

        for entity_name, record in vectors_dict.items():
            page_vector = record.get("vector", [])
            similarity = self.compute_cosine_similarity(query_vector, page_vector)
            
            # Additional exact/partial keyword boost
            lower_query = query_str.lower()
            if entity_name.lower() in lower_query or lower_query in entity_name.lower():
                similarity = min(1.0, similarity + 0.25)
            elif any(q_word in record.get("snippet", "").lower() for q_word in lower_query.split() if len(q_word) > 2):
                similarity = min(1.0, similarity + 0.10)

            scored_results.append((similarity, record))

        # Sort by similarity score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)

        results: List[SemanticSearchResult] = []
        for score, record in scored_results[:top_k]:
            results.append(SemanticSearchResult(
                entity_name=record["entity_name"],
                filename=record["filename"],
                entity_type=record["entity_type"],
                similarity_score=round(float(score), 4),
                snippet=record["snippet"],
                links_to=record.get("links_to", [])
            ))

        return SemanticSearchResponse(
            query=query_str,
            total_results=len(results),
            results=results
        )

# Default singleton instance
vector_service = VectorService()
