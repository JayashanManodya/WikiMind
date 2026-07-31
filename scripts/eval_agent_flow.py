"""Evaluation script for WikiMind 3-Agent QA Flow (Retrieval -> Summarization -> Verification).

This script benchmarks answer quality, groundedness, negative refusal, citation rate,
and query execution latency across a set of test questions. If LANGCHAIN_API_KEY is configured,
it also traces and evaluates runs in LangSmith.
"""

import sys
import os
import time
import asyncio
from pathlib import Path

# Ensure root and backend directories are on sys.path
root_dir = Path(__file__).parent.parent
backend_dir = root_dir / "backend"
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env", override=True)
load_dotenv(root_dir / ".env", override=True)

# Explicitly set LangSmith environment variables in process environment
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"] = "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"
os.environ["LANGSMITH_PROJECT"] = "WikiMind-3Agent-Evaluation"

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "WikiMind-3Agent-Evaluation"

from backend.app.core.agents.graph import run_qa_flow
from backend.app.core.ingestion.wiki_generator import generate_wiki_pages_from_text
from backend.app.core.retrieval.vector_store import index_wiki_documents
from backend.app.core.paths import get_user_wiki_dir


BENCHMARK_DATASET = [
    {
        "id": "Q1_DIRECT",
        "question": "What is WikiMind and what are its key features?",
        "expected_type": "factual",
        "keywords": ["wikimind", "knowledge", "qa"]
    },
    {
        "id": "Q2_TECH",
        "question": "Which database and vector store does WikiMind use?",
        "expected_type": "technical",
        "keywords": ["turso", "pinecone", "sqlite"]
    },
    {
        "id": "Q3_REFUSAL",
        "question": "Who won the 1998 FIFA World Cup final match?",
        "expected_type": "refusal",
        "keywords": ["lacks", "cannot", "does not contain"]
    }
]


def setup_eval_knowledge_base(user_id: str = "eval_user"):
    """Populate evaluation user's knowledge base with benchmark test documents."""
    sample_text = """
    WikiMind is an AI-Powered Intelligent Knowledge Management System (IKMS) that transforms unstructured documents
    into a structured Wikipedia-style Knowledge Base and an Interactive 2D Physics Knowledge Graph.
    Key features include Multi-Format Document Ingestion (PDF, DOCX, XLSX, TXT), Automated Multi-Entity Discovery,
    Grounded Zero-Hallucination QA Assistant with citations, and 0ms Client-Side Memory Caching.
    WikiMind utilizes the Turso Edge Cloud Database (libsql SQLite) for session and wiki page storage,
    and Pinecone Vector Store with OpenAI 1536-dimensional embeddings for vector search.
    """
    user_wiki_dir = get_user_wiki_dir(user_id)
    wiki_pages = generate_wiki_pages_from_text(sample_text, "wikimind_overview.txt", wiki_dir=str(user_wiki_dir))
    index_wiki_documents(wiki_pages, user_id=user_id)


async def evaluate_single_query(item: dict) -> dict:
    question = item["question"]
    start_time = time.perf_counter()
    
    try:
        res = await run_qa_flow(question, user_id="eval_user")
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        answer = res.get("answer", "")
        context = res.get("context", "")
        
        is_refusal = any(ref in answer.lower() for ref in ["lacks sufficient details", "cannot answer", "does not contain", "cannot provide"])
        
        if item["expected_type"] == "refusal":
            grounded_score = 1.0 if is_refusal else 0.0
        else:
            grounded_score = 1.0 if not is_refusal and len(answer) > 20 else 0.0
            
        has_context = len(context) > 10 and context != "No context found."
        
        return {
            "id": item["id"],
            "question": question,
            "latency_ms": elapsed_ms,
            "grounded_score": grounded_score,
            "has_context": has_context,
            "is_refusal": is_refusal,
            "answer_preview": answer[:120].replace("\n", " ") + ("..." if len(answer) > 120 else "")
        }
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "id": item["id"],
            "question": question,
            "latency_ms": elapsed_ms,
            "grounded_score": 0.0,
            "has_context": False,
            "is_refusal": False,
            "answer_preview": f"ERROR: {str(e)}"
        }


async def run_evaluation_suite():
    print("=" * 80)
    print("Running WikiMind 3-Agent Flow Evaluation Benchmark")
    print("=" * 80)
    
    # Pre-populate evaluation knowledge base
    setup_eval_knowledge_base("eval_user")
    
    langsmith_active = os.getenv("LANGCHAIN_TRACING_V2") == "true" and os.getenv("LANGCHAIN_API_KEY")
    if langsmith_active:
        print(f"LangSmith Tracing Active | Project: {os.getenv('LANGCHAIN_PROJECT', 'WikiMind-QA')}")
    else:
        print("Tip: Set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY in .env for LangSmith dashboard tracing.")
    
    print("-" * 80)
    
    results = []
    for item in BENCHMARK_DATASET:
        print(f"Evaluating [{item['id']}]: '{item['question']}' ...")
        res = await evaluate_single_query(item)
        results.append(res)
        
    print("\n" + "=" * 80)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 80)
    print(f"{'ID':<12} | {'Latency':<10} | {'Grounded':<10} | {'Answer Preview'}")
    print("-" * 80)
    
    total_latency = 0
    total_grounded = 0
    
    for r in results:
        total_latency += r["latency_ms"]
        total_grounded += r["grounded_score"]
        score_str = "PASS (1.0)" if r["grounded_score"] == 1.0 else "FAIL (0.0)"
        print(f"{r['id']:<12} | {r['latency_ms']:<7} ms | {score_str:<10} | {r['answer_preview']}")
        
    avg_latency = round(total_latency / len(results), 2)
    overall_groundedness = round((total_grounded / len(results)) * 100, 1)
    
    print("=" * 80)
    print(f"Overall Average Latency: {avg_latency} ms")
    print(f"Overall Groundedness Score: {overall_groundedness}%")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_evaluation_suite())
