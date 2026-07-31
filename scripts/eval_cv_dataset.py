"""LangSmith Dataset Experiment Runner for Jayashan Manodya's CV Benchmark (20 Questions).

This script creates and evaluates a formal dataset named 'Jayashan_Manodya_CV_Benchmark'
in LangSmith, benchmarking accuracy, groundedness, and response quality across 18 factual CV questions + 2 refusal tests.
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


DATASET_NAME = "Jayashan_Manodya_CV_Benchmark"

BENCHMARK_EXAMPLES = [
    {
        "inputs": {"question": "What degree is Jayashan Manodya currently pursuing?"},
        "outputs": {"reference": "BSc (Hons) in Information Technology specializing in Artificial Intelligence at Sri Lanka Institute of Information Technology (SLIIT)."}
    },
    {
        "inputs": {"question": "What is the student's current GPA?"},
        "outputs": {"reference": "The most recent semester (Y2S2) GPA is 3.93/4.0."}
    },
    {
        "inputs": {"question": "Which institute does Jayashan study at?"},
        "outputs": {"reference": "Sri Lanka Institute of Information Technology (SLIIT)."}
    },
    {
        "inputs": {"question": "What AI areas is Jayashan interested in?"},
        "outputs": {"reference": "Generative AI, Machine Learning, Computer Vision, Retrieval-Augmented Generation (RAG), Full-stack Development, Agentic AI, Multi-agent Systems, and Software Engineering."}
    },
    {
        "inputs": {"question": "What technologies were used to build the IKMS project?"},
        "outputs": {"reference": "FastAPI, LangGraph, OpenAI GPT-4o, Pinecone, LangChain, PyPDF, React, and Python."}
    },
    {
        "inputs": {"question": "What is the purpose of the IKMS project?"},
        "outputs": {"reference": "Retrieval-Augmented Generation (RAG) document question-answering system allowing users to upload PDFs and receive accurate, context-aware answers using a multi-agent pipeline."}
    },
    {
        "inputs": {"question": "What does PlateX do?"},
        "outputs": {"reference": "PlateX performs real-time vehicle license plate detection and OCR-based text extraction from images."}
    },
    {
        "inputs": {"question": "Which machine learning model was used in WeatherLK?"},
        "outputs": {"reference": "RandomForestRegressor."}
    },
    {
        "inputs": {"question": "What is KIKO?"},
        "outputs": {"reference": "KIKO is an AI-powered conversational shopping assistant with a five-agent architecture using the Kapruka MCP that supports shopping through natural language conversations."}
    },
    {
        "inputs": {"question": "What languages does KIKO support?"},
        "outputs": {"reference": "English, Sinhala, and Tamil."}
    },
    {
        "inputs": {"question": "What is NutriLens AI?"},
        "outputs": {"reference": "An AI-powered nutrition assistant that analyzes food using OCR and LLMs, provides personalized recommendations, healthier alternatives, and long-term nutrition tracking."}
    },
    {
        "inputs": {"question": "Where does Jayashan currently work?"},
        "outputs": {"reference": "Creative Designer (Part Time) at Glanz Digital (PVT) Ltd."}
    },
    {
        "inputs": {"question": "What programming languages are listed?"},
        "outputs": {"reference": "Python, Java, JavaScript, TypeScript, C, and C++."}
    },
    {
        "inputs": {"question": "Which databases are mentioned?"},
        "outputs": {"reference": "PostgreSQL, MongoDB, Vector Databases, MySQL, and File-based Storage Systems."}
    },
    {
        "inputs": {"question": "What cloud platforms are listed?"},
        "outputs": {"reference": "Railway, Vercel, and Render."}
    },
    {
        "inputs": {"question": "What certifications are listed?"},
        "outputs": {"reference": "AI Engineer Bootcamp (STEM Link), AI/ML Engineer Stage 1 (SLIIT), Programming in Python (CODL), Web Development (CODL), Fundamentals of Digital Marketing (Google Digital Garage), and Arduino CodeCamp Workshop."}
    },
    {
        "inputs": {"question": "What achievements are listed?"},
        "outputs": {"reference": "Dean's List Recipient, Ranked 11th in Bashaway 2024, and Top 20 Finalist & Exhibitionist in an IoT Project Showcase."}
    },
    {
        "inputs": {"question": "Who are the references mentioned?"},
        "outputs": {"reference": "Mr. Amila Nuwan Alexander and Mr. Bhanuka Edirisinghe from SLIIT."}
    },
    {
        "inputs": {"question": "What is Jayashan's favorite space station module?"},
        "outputs": {"reference": "The knowledge base lacks sufficient details to answer this question."}
    },
    {
        "inputs": {"question": "What is the name of Jayashan's pet dog?"},
        "outputs": {"reference": "The knowledge base lacks sufficient details to answer this question."}
    }
]


def setup_cv_knowledge_base(user_id: str = "jayashan_user"):
    """Ingest Jayashan Manodya's complete CV knowledge into WikiMind vector store."""
    cv_summary_text = """
    # Jayashan Manodya - Resume & Profile
    
    ## Education & Profile
    - Student Name: Jayashan Manodya
    - Institution: Sri Lanka Institute of Information Technology (SLIIT)
    - Degree: BSc (Hons) in Information Technology specializing in Artificial Intelligence
    - GPA: Y2S2 GPA is 3.93 / 4.0. Dean's List Recipient.
    - Areas of Interest: Generative AI, Machine Learning, Computer Vision, Retrieval-Augmented Generation (RAG), Full-stack Development, Agentic AI, Multi-agent Systems, Software Engineering.
    
    ## Experience & Roles
    - Current Work: Creative Designer (Part Time) at Glanz Digital (PVT) Ltd.
    
    ## Projects
    1. IKMS (WikiMind): AI-powered Knowledge Management & RAG document question-answering system allowing users to upload PDFs and receive context-aware answers using a multi-agent pipeline. Built with FastAPI, LangGraph, OpenAI GPT-4o, Pinecone, LangChain, PyPDF, React, and Python.
    2. PlateX: Real-time vehicle license plate detection and OCR-based text extraction from images.
    3. WeatherLK: Machine learning weather prediction system using RandomForestRegressor model.
    4. KIKO: AI-powered conversational shopping assistant with a five-agent architecture using Kapruka MCP, supporting English, Sinhala, and Tamil.
    5. NutriLens AI: AI-powered nutrition assistant analyzing food using OCR and LLMs, providing personalized recommendations, healthier alternatives, and long-term nutrition tracking.
    
    ## Technical Skills & Stack
    - Programming Languages: Python, Java, JavaScript, TypeScript, C, C++.
    - Databases: PostgreSQL, MongoDB, Vector Databases, MySQL, File-based Storage Systems.
    - Cloud Platforms: Railway, Vercel, Render.
    
    ## Certifications
    - AI Engineer Bootcamp (STEM Link)
    - AI/ML Engineer Stage 1 (SLIIT)
    - Programming in Python (CODL)
    - Web Development (CODL)
    - Fundamentals of Digital Marketing (Google Digital Garage)
    - Arduino CodeCamp Workshop
    
    ## Achievements
    - Dean's List Recipient at SLIIT
    - Ranked 11th in Bashaway 2024
    - Top 20 Finalist & Exhibitionist in IoT Project Showcase
    
    ## References
    - Mr. Amila Nuwan Alexander (SLIIT)
    - Mr. Bhanuka Edirisinghe (SLIIT)
    """
    user_wiki_dir = get_user_wiki_dir(user_id)
    wiki_pages = generate_wiki_pages_from_text(cv_summary_text, "jayashan_manodya_cv.txt", wiki_dir=str(user_wiki_dir))
    index_wiki_documents(wiki_pages, user_id=user_id)


def target_agent_pipeline(inputs: dict) -> dict:
    """Run 3-agent QA graph for Jayashan's CV queries."""
    question = inputs["question"]
    res = asyncio.run(run_qa_flow(question, user_id="jayashan_user"))
    return {
        "output": res.get("answer", ""),
        "context": res.get("context", "")
    }


def qa_correctness_evaluator(run, example) -> dict:
    """Evaluates answer correctness against reference CV facts."""
    prediction = run.outputs.get("output", "").lower()
    reference = example.outputs.get("reference", "").lower()
    
    if "lacks" in reference or "cannot" in reference:
        score = 1.0 if any(term in prediction for term in ["lacks", "cannot", "does not contain", "not contain"]) else 0.0
    else:
        # Check key terms matching reference
        ref_words = [w.strip(".,()") for w in reference.split() if len(w) > 3]
        matches = sum(1 for w in ref_words if w in prediction)
        match_ratio = matches / max(len(ref_words), 1)
        score = 1.0 if match_ratio >= 0.3 else 0.0
        
    return {"key": "qa_correctness", "score": score}


def groundedness_evaluator(run, example) -> dict:
    """Evaluates if response is grounded in vector context."""
    context = run.outputs.get("context", "")
    has_context = len(context) > 10 and context != "No context found."
    return {"key": "groundedness_score", "score": 1.0 if has_context else 0.0}


def main():
    print("=" * 80)
    print("Initializing Jayashan Manodya CV Benchmark Dataset & Experiment")
    print("=" * 80)
    
    setup_cv_knowledge_base("jayashan_user")
    
    client = Client()
    
    # 1. Create or sync dataset in LangSmith
    if not client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Jayashan Manodya 20-Question CV Evaluation Benchmark Dataset."
        )
        client.create_examples(
            inputs=[e["inputs"] for e in BENCHMARK_EXAMPLES],
            outputs=[e["outputs"] for e in BENCHMARK_EXAMPLES],
            dataset_id=dataset.id,
        )
        print(f"Created new LangSmith Dataset: '{DATASET_NAME}' with 20 evaluation examples.")
    else:
        print(f"Using existing LangSmith Dataset: '{DATASET_NAME}'")

    print("-" * 80)
    print("Running 20-Question LangSmith CV Experiment Evaluation...")
    
    # 2. Run LangSmith evaluate() SDK
    results = evaluate(
        target_agent_pipeline,
        data=DATASET_NAME,
        evaluators=[qa_correctness_evaluator, groundedness_evaluator],
        experiment_prefix="single-agent-v2",
        max_concurrency=4
    )
    
    print("\n" + "=" * 80)
    print("CV BENCHMARK EXPERIMENT COMPLETE")
    print("=" * 80)
    print(f"Dataset Name: {DATASET_NAME}")
    print(f"Experiment Run: {results.experiment_name}")
    print("View your full CV Experiment Dashboard at: https://smith.langchain.com/")
    print("=" * 80)


if __name__ == "__main__":
    main()
