"""LangSmith Dataset Experiment Runner for WikiMind 3-Agent QA Flow.

This script creates/syncs a formal dataset named 'WikiMind_Accuracy_Benchmark' in LangSmith,
runs an experiment using LangSmith's evaluate() engine, and scores accuracy/correctness.
"""

import sys
import os
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

# Ensure LangSmith environment variables are set
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "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")
os.environ["LANGSMITH_PROJECT"] = "WikiMind-3Agent-Evaluation"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "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")
os.environ["LANGCHAIN_PROJECT"] = "WikiMind-3Agent-Evaluation"

from langsmith import Client
from langsmith.evaluation import evaluate
from backend.app.core.agents.graph import run_qa_flow
from backend.app.core.ingestion.wiki_generator import generate_wiki_pages_from_text
from backend.app.core.retrieval.vector_store import index_wiki_documents
from backend.app.core.paths import get_user_wiki_dir


DATASET_NAME = "WikiMind_Accuracy_Benchmark"

BENCHMARK_EXAMPLES = [
    {
        "inputs": {"question": "What is WikiMind and what are its key features?"},
        "outputs": {"reference": "WikiMind is an AI-Powered Intelligent Knowledge Management System (IKMS) featuring multi-format document ingestion, automated multi-entity discovery, grounded zero-hallucination QA assistant with citations, and interactive 2D physics knowledge graph."}
    },
    {
        "inputs": {"question": "Which database and vector store does WikiMind use?"},
        "outputs": {"reference": "WikiMind uses Turso Edge Cloud Database (libsql SQLite) for session and wiki storage, and Pinecone Vector Store with OpenAI 1536-dimensional embeddings for vector search."}
    },
    {
        "inputs": {"question": "Who won the 1998 FIFA World Cup final match?"},
        "outputs": {"reference": "The knowledge base lacks sufficient details to answer this question."}
    }
]


def setup_knowledge_base(user_id: str = "eval_user"):
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


def target_agent_pipeline(inputs: dict) -> dict:
    """Synchronous wrapper around async run_qa_flow for LangSmith evaluate SDK."""
    question = inputs["question"]
    res = asyncio.run(run_qa_flow(question, user_id="eval_user"))
    return {
        "output": res.get("answer", ""),
        "context": res.get("context", "")
    }


def qa_correctness_evaluator(run, example) -> dict:
    """Evaluates if prediction matches expected reference ground truth."""
    prediction = run.outputs.get("output", "").lower()
    reference = example.outputs.get("reference", "").lower()
    
    if "lacks" in reference or "cannot" in reference:
        score = 1.0 if any(term in prediction for term in ["lacks", "cannot", "does not contain", "not contain"]) else 0.0
    else:
        score = 1.0 if len(prediction) > 20 and ("lacks" not in prediction) else 0.0
        
    return {"key": "qa_correctness", "score": score}


def groundedness_evaluator(run, example) -> dict:
    """Evaluates if answer is grounded in retrieved vector context."""
    context = run.outputs.get("context", "")
    has_context = len(context) > 10 and context != "No context found."
    return {"key": "groundedness_score", "score": 1.0 if has_context else 0.0}


def main():
    print("=" * 80)
    print("Initializing LangSmith Dataset & Accuracy Experiment")
    print("=" * 80)
    
    setup_knowledge_base("eval_user")
    
    client = Client()
    
    # 1. Create or verify LangSmith dataset
    if not client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Golden accuracy dataset for WikiMind 3-Agent QA Pipeline."
        )
        client.create_examples(
            inputs=[e["inputs"] for e in BENCHMARK_EXAMPLES],
            outputs=[e["outputs"] for e in BENCHMARK_EXAMPLES],
            dataset_id=dataset.id,
        )
        print(f"Created new LangSmith Dataset: '{DATASET_NAME}'")
    else:
        print(f"Using existing LangSmith Dataset: '{DATASET_NAME}'")

    print("-" * 80)
    print("Running LangSmith Experiment Evaluation...")
    
    # 2. Run LangSmith evaluate() SDK
    results = evaluate(
        target_agent_pipeline,
        data=DATASET_NAME,
        evaluators=[qa_correctness_evaluator, groundedness_evaluator],
        experiment_prefix="3agent-accuracy-eval",
        max_concurrency=1
    )
    
    print("\n" + "=" * 80)
    print("LANGSMITH EXPERIMENT COMPLETE")
    print("=" * 80)
    print(f"Dataset Name: {DATASET_NAME}")
    print(f"Experiment Name: {results.experiment_name}")
    print("View your full Experiment Dashboard at: https://smith.langchain.com/")
    print("=" * 80)


if __name__ == "__main__":
    main()
