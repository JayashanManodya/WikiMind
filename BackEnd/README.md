# IKMS RAG Agent System — Backend

> **Intelligent Knowledge Management System** powered by a multi-agent Retrieval-Augmented Generation (RAG) pipeline built with LangGraph, FastAPI, Pinecone, and OpenAI.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [Core Components](#5-core-components)
   - [5.1 API Layer](#51-api-layer)
   - [5.2 Multi-Agent Pipeline](#52-multi-agent-pipeline)
   - [5.3 LangGraph Orchestration](#53-langgraph-orchestration)
   - [5.4 Vector Store & Retrieval](#54-vector-store--retrieval)
   - [5.5 LLM Factory](#55-llm-factory)
   - [5.6 Configuration](#56-configuration)
6. [API Reference](#6-api-reference)
7. [Data Models](#7-data-models)
8. [Agent Prompts](#8-agent-prompts)
9. [Environment Variables](#9-environment-variables)
10. [Installation & Setup](#10-installation--setup)
11. [Running the Application](#11-running-the-application)
12. [Deployment](#12-deployment)
13. [Design Patterns](#13-design-patterns)
14. [Flow Diagram](#14-flow-diagram)

---

## 1. Project Overview

**IKMS RAG Agent System** is a backend service that implements a **multi-agent Retrieval-Augmented Generation (RAG)** pipeline for intelligent document question-answering. Users can:

- **Upload PDF documents** to be indexed into a Pinecone vector store.
- **Ask natural language questions** about those documents.
- Receive **verified, grounded answers** produced by a 4-stage agentic pipeline (Planning → Retrieval → Summarization → Verification).

The system is designed for **serverless deployment** (Vercel / Heroku-compatible) and processes PDFs entirely **in-memory** with no disk writes.

---

## 2. Architecture Overview

```
User Prompt (HTTP POST /qa)
        │
        ▼
  ┌─────────────────┐
  │   FastAPI API   │   (app/api.py)
  └────────┬────────┘
           │ async call
           ▼
  ┌─────────────────────────────────────────────────────┐
  │              LangGraph QA Graph                     │
  │                                                     │
  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
  │  │ Planning │→ │Retrieval │→ │ Summarization    │  │
  │  │  Agent   │  │  Agent   │  │    Agent         │  │
  │  └──────────┘  └─────┬────┘  └────────┬─────────┘  │
  │                      │               │             │
  │               ┌──────▼──────┐  ┌─────▼──────────┐ │
  │               │  Pinecone   │  │  Verification  │ │
  │               │ Vector Store│  │    Agent       │ │
  │               └─────────────┘  └────────────────┘ │
  └─────────────────────────────────────────────────────┘
           │
           ▼
  Final Verified Answer (HTTP Response)
```

---

## 3. Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Runtime** | Python | ≥ 3.12 |
| **Web Framework** | FastAPI | ≥ 0.128.0 |
| **ASGI Server** | Uvicorn | ≥ 0.38.0 |
| **Agent Orchestration** | LangGraph | ≥ 1.0.4 |
| **LLM Integration** | LangChain | ≥ 1.2.6 |
| **LLM Provider (Chat)** | OpenAI (`gpt-4o-mini`) | via `langchain-openai ≥ 1.1.0` |
| **LLM Provider (Alt)** | Google Gemini | via `langchain-google-genai ≥ 4.2.0` |
| **Embedding Model** | OpenAI `text-embedding-3-small` | via `langchain-openai` |
| **Vector Database** | Pinecone | `pinecone-client ≥ 6.0.0` |
| **Vector Store Integration** | LangChain-Pinecone | ≥ 0.2.13 |
| **PDF Parsing** | PyPDF | ≥ 6.4.1 |
| **PDF Loader (disk)** | LangChain Community `PyPDFLoader` | ≥ 0.3.0 |
| **Text Splitting** | LangChain Text Splitters | ≥ 1.0.0 |
| **Settings Management** | Pydantic Settings | ≥ 2.0.0 |
| **Environment Variables** | python-dotenv | ≥ 1.2.1 |
| **File Uploads** | python-multipart | ≥ 0.0.20 |
| **Package Manager** | uv (via `pyproject.toml`) | — |

---

## 4. Project Structure

```
backend/
├── main.py                         # Entry point — launches uvicorn
├── Procfile                        # Heroku/platform process definition
├── pyproject.toml                  # Project metadata & dependencies (PEP 518)
├── uv.lock                         # Locked dependency graph
├── .env                            # Local environment variables (not committed)
├── .python-version                 # Python version pin (3.12)
│
├── app/
│   ├── __init__.py
│   ├── api.py                      # FastAPI app, routes, CORS
│   ├── models.py                   # Pydantic request/response models
│   │
│   ├── core/
│   │   ├── config.py               # Settings (pydantic-settings, singleton)
│   │   │
│   │   ├── agents/                 # Multi-agent RAG implementation
│   │   │   ├── agents.py           # Agent definitions and node functions
│   │   │   ├── graph.py            # LangGraph StateGraph compilation
│   │   │   ├── state.py            # QAState TypedDict schema
│   │   │   ├── prompts.py          # System prompts for all 4 agents
│   │   │   └── tools.py            # retrieval_tool (LangChain @tool)
│   │   │
│   │   ├── retrieval/              # Pinecone vector store layer
│   │   │   ├── vector_store.py     # Pinecone init, retrieve, index functions
│   │   │   └── serialization.py    # Document → formatted string converter
│   │   │
│   │   └── llm/
│   │       └── factory.py          # ChatOpenAI factory (lru_cache singleton)
│   │
│   └── services/
│       └── qa_service.py           # Service façade: bridges API ↔ LangGraph
│
└── data/
    └── uploads/                    # (Runtime) temp uploads — not used in serverless mode
```

---

## 5. Core Components

### 5.1 API Layer

**File:** `app/api.py`

FastAPI application with 4 endpoints and CORS middleware configured for all origins (`*`).

```python
app = FastAPI(title="IKMS RAG Agent System")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], ...)
```

| Route | Method | Handler | Description |
|-------|--------|---------|-------------|
| `/` | GET | `root()` | API metadata and endpoint listing |
| `/health` | GET | `health_check()` | Liveness probe — returns `{"status": "ok"}` |
| `/qa` | POST | `qa_endpoint()` | Ask a question → runs multi-agent pipeline |
| `/index-pdf` | POST | `index_pdf_endpoint()` | Upload & index a PDF in-memory |

**PDF Indexing flow:**
1. Receives `UploadFile` (multipart form-data)
2. Validates `.pdf` extension
3. Reads raw bytes with `await file.read()`
4. Calls `index_documents_from_bytes(file_bytes, filename)` — **no disk writes**
5. Returns `{"message": "...", "chunks": <int>}`

---

### 5.2 Multi-Agent Pipeline

**Directory:** `app/core/agents/`

The system implements a **4-stage linear multi-agent pipeline**:

#### Agent 1 — Planning Agent (`planning_node`)
- **Role:** Query analysis and decomposition
- **Input:** Raw user question
- **Output:** `plan` (string) + `sub_questions` (list of focused search queries)
- **Behavior:** Determines if the question is simple (1 sub-question) or complex (multiple sub-questions for targeted retrieval)
- **Model:** `gpt-4o-mini` (temperature=0.0)

#### Agent 2 — Retrieval Agent (`retrieval_node`)
- **Role:** Parallel vector store retrieval
- **Input:** `sub_questions` list from Planning Agent
- **Output:** `context` string (combined chunks from Pinecone)
- **Behavior:** Fires parallel `asyncio.gather()` calls for each sub-question, each calling the `retrieval_tool` which searches top-k=4 Pinecone chunks
- **Tool:** `retrieval_tool` (LangChain `@tool` with `response_format="content_and_artifact"`)
- **Model:** `gpt-4o-mini` bound with `retrieval_tool`

#### Agent 3 — Summarization Agent (`summarization_node`)
- **Role:** Draft answer generation
- **Input:** `question` + `context`
- **Output:** `draft_answer` (string)
- **Behavior:** Generates a grounded answer using ONLY the retrieved context. Explicitly states if context is insufficient.
- **Model:** `gpt-4o-mini` (temperature=0.0)

#### Agent 4 — Verification Agent (`verification_node`)
- **Role:** Hallucination elimination and fact-checking
- **Input:** `question` + `context` + `draft_answer`
- **Output:** `answer` (final verified string)
- **Behavior:** Cross-checks every claim in the draft against context, removes or corrects unsupported information, returns only the corrected answer text
- **Model:** `gpt-4o-mini` (temperature=0.0)

#### Agent Factory (`create_agent`)
All agents are created via a common factory function in `agents.py`:
```python
def create_agent(model, tools, system_prompt) -> Agent:
    # Optionally binds tools via model.bind_tools(tools)
    # Returns object with invoke() and ainvoke() methods
```

---

### 5.3 LangGraph Orchestration

**File:** `app/core/agents/graph.py`

The pipeline is implemented as a **LangGraph `StateGraph`** using a `TypedDict`-based state:

```python
class QAState(TypedDict):
    question:       str
    context:        str | None
    draft_answer:   str | None
    answer:         str | None
    plan:           str | None
    sub_questions:  list[str] | None
```

**Graph Topology (Linear DAG):**
```
START → planning → retrieval → summarization → verification → END
```

**Key design decisions:**
- `@lru_cache(maxsize=1)` on `get_qa_graph()` → graph compiled once, reused as singleton
- `graph.ainvoke(initial_state)` → fully async execution
- Each node function receives `QAState` and returns a partial dict to merge into state

---

### 5.4 Vector Store & Retrieval

**File:** `app/core/retrieval/vector_store.py`

Wraps **Pinecone** via `langchain-pinecone`.

| Function | Description |
|----------|-------------|
| `_get_vector_store()` | Creates `PineconeVectorStore` instance (lru_cache singleton) using `OpenAIEmbeddings` |
| `get_retriever(k)` | Returns a LangChain retriever interface from the vector store |
| `retrieve(query, k)` | Direct similarity search returning `List[Document]` |
| `index_documents(file_path)` | Indexes a PDF from disk (legacy/local dev path) |
| `index_documents_from_bytes(bytes, name)` | **Primary path** — indexes PDF from raw bytes (no disk I/O) |

**Chunking Strategy:**
- Splitter: `RecursiveCharacterTextSplitter`
- `chunk_size = 500` characters
- `chunk_overlap = 50` characters

**Embedding Model:** `text-embedding-3-small` (OpenAI)  
**Vector DB:** Pinecone (index name: `ikms-rag-agent-system`)  
**Similarity Metric:** Default Pinecone cosine similarity  
**Retrieval top-k:** 4 (configurable via `retrieval_k` setting)

**Serialization (`serialization.py`):**
```
Chunk 1 (page=3): ...text content...
Chunk 2 (page=5): ...text content...
```

---

### 5.5 LLM Factory

**File:** `app/core/llm/factory.py`

```python
@lru_cache(maxsize=1)
def create_chat_model(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(model=settings.openai_model_name, ...)
```

- Uses **OpenAI `gpt-4o-mini`** as the default chat model
- Temperature set to `0.0` for **deterministic, reproducible** outputs across all agents
- `lru_cache` singleton — model instantiated once per process
- `ChatGoogleGenerativeAI` is also imported for potential Gemini fallback

---

### 5.6 Configuration

**File:** `app/core/config.py`

Uses **Pydantic Settings v2** with automatic env-file detection:

```python
_ENV_FILE = ".env" if os.path.exists(".env") else None  # Serverless-safe
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `openai_api_key` | str | *required* | OpenAI API key |
| `openai_model_name` | str | *required* | Chat model name (e.g., `gpt-4o-mini`) |
| `openai_embedding_model_name` | str | *required* | Embedding model (e.g., `text-embedding-3-small`) |
| `pinecone_api_key` | str | *required* | Pinecone API key |
| `pinecone_index_name` | str | *required* | Pinecone index name |
| `pinecone_environment` | str | `""` | Pinecone environment (optional) |
| `retrieval_k` | int | `4` | Top-k chunks retrieved per query |

Settings are loaded via `get_settings()` — a **lazy singleton** using a module-level global:
```python
settings: Settings | None = None

def get_settings() -> Settings:
    global settings
    if settings is None:
        settings = Settings()
    return settings
```

---

## 6. API Reference

### `GET /`
Returns API metadata.

**Response:**
```json
{
  "name": "IKMS RAG Agent System",
  "version": "1.0.0",
  "endpoints": {
    "qa": "POST /qa",
    "index_pdf": "POST /index-pdf",
    "health": "GET /health"
  }
}
```

---

### `GET /health`
Liveness check.

**Response:**
```json
{ "status": "ok" }
```

---

### `POST /qa`
Ask a question using the multi-agent RAG pipeline.

**Request Body (JSON):**
```json
{ "question": "What are the advantages of vector databases?" }
```

**Response Body (JSON):**
```json
{
  "answer": "Vector databases offer advantages such as...",
  "context": "Chunk 1 (page=3): ... \n\nChunk 2 (page=7): ..."
}
```

**Error:** `500` with `detail` string on pipeline failure.

---

### `POST /index-pdf`
Upload a PDF file to be chunked and indexed into Pinecone.

**Request:** `multipart/form-data` with field `file` (`.pdf` only)

**Response:**
```json
{
  "message": "Successfully indexed <filename>",
  "chunks": 42
}
```

**Error:** `400` if file is not a PDF; `500` on indexing failure (includes full traceback).

---

## 7. Data Models

**File:** `app/models.py`

```python
class QuestionRequest(BaseModel):
    question: str          # User's natural language question

class QAResponse(BaseModel):
    answer: str            # Final verified answer from the pipeline
    context: str           # Retrieved context chunks shown to the user
```

**Internal State (`QAState` TypedDict):**

```python
class QAState(TypedDict):
    question:      str              # Original user question
    plan:          str | None       # Planning agent output
    sub_questions: list[str] | None # Decomposed search queries
    context:       str | None       # Retrieved Pinecone context
    draft_answer:  str | None       # Summarization agent draft
    answer:        str | None       # Final verified answer
```

---

## 8. Agent Prompts

**File:** `app/core/agents/prompts.py`

| Agent | Prompt Key | Core Behavior |
|-------|-----------|---------------|
| Planning | `PLANNING_AGENT_PROMPT` | Classify as simple/complex, generate sub-questions in `Plan: / Sub-questions:` format |
| Retrieval | `RETRIEVAL_SYSTEM_PROMPT` | Call `retrieval_tool` for each query, consolidate context, do NOT answer directly |
| Summarization | `SUMMARIZATION_SYSTEM_PROMPT` | Generate answer from ONLY provided context, admit if context insufficient |
| Verification | `VERIFICATION_SYSTEM_PROMPT` | Check every claim, remove hallucinations, return only the final answer text |

---

## 9. Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_EMBEDDING_MODEL_NAME=text-embedding-3-small

# Pinecone
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=ikms-rag-agent-system

# Google (optional, for Gemini fallback)
GOOGLE_API_KEY=AIza...
```

> **Note:** On serverless platforms (Vercel, Railway, etc.), set these as platform environment variables instead of using a `.env` file. The `config.py` automatically skips `.env` loading when the file doesn't exist.

---

## 10. Installation & Setup

### Prerequisites
- Python ≥ 3.12
- [`uv`](https://github.com/astral-sh/uv) package manager (recommended) or `pip`
- A Pinecone account with a created index
- An OpenAI account with API access

### Step 1 — Clone the repository
```bash
git clone <repository-url>
cd ikms-rag-agent-system/backend
```

### Step 2 — Create & activate virtual environment

**Using `uv` (recommended):**
```bash
uv sync
```

**Using `pip`:**
```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # macOS/Linux
pip install -e .
```

### Step 3 — Configure environment variables
```bash
copy .env.example .env       # Windows
cp .env.example .env         # macOS/Linux
# Edit .env with your actual API keys
```

### Step 4 — Create Pinecone Index
In your Pinecone console:
- **Index name:** `ikms-rag-agent-system`
- **Dimensions:** `1536` (matches `text-embedding-3-small`)
- **Metric:** `cosine`

---

## 11. Running the Application

### Development (auto-reload)
```bash
python main.py
```
Starts Uvicorn on `http://0.0.0.0:8000` with hot-reload enabled.

### Production
```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000
```

### Interactive API Docs
Once running, visit:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 12. Deployment

### Heroku / Render / Railway
The `Procfile` is included:
```
web: uvicorn app.api:app --host $SERVER_HOST --port $SERVER_PORT
```
Set `SERVER_HOST` and `SERVER_PORT` as platform environment variables.

### Vercel (Serverless)
- The system is **serverless-compatible**: PDF indexing uses `index_documents_from_bytes()` which processes PDFs entirely in-memory using `pypdf`
- All environment variables are injected by Vercel — no `.env` file needed
- The `config.py` detects the absence of `.env` and skips file loading gracefully

---

## 13. Design Patterns

| Pattern | Where Used | Purpose |
|---------|-----------|---------|
| **Singleton (lru_cache)** | `get_qa_graph()`, `_get_vector_store()`, `create_chat_model()` | Avoid re-instantiating expensive objects (Pinecone client, LLM) per request |
| **Lazy initialization** | `get_settings()` | Settings loaded on first access, not at import time |
| **Service Layer** | `qa_service.py` | Decouples FastAPI routes from LangGraph implementation details |
| **Factory Function** | `create_agent()` in `agents.py` | Uniform agent construction with optional tool binding |
| **State Machine** | LangGraph `StateGraph` + `QAState` | Typed, explicit state flow between agents |
| **Parallel Execution** | `asyncio.gather()` in `retrieval_node` | Concurrent vector store searches for multiple sub-questions |
| **Content+Artifact Tool** | `retrieval_tool` with `response_format="content_and_artifact"` | Returns both human-readable context string and raw Document objects |

---

## 14. Flow Diagram

```
User Question
     │
     ▼
[POST /qa endpoint]
     │
     ▼
[qa_service.answer_question(question)]
     │
     ▼
[run_qa_flow(question)] — LangGraph async invocation
     │
     ├─► [planning_node]
     │       ├─ LLM call: gpt-4o-mini (temp=0.0)
     │       ├─ Parses "Plan:" and "Sub-questions:" from response
     │       └─ Updates state: plan, sub_questions
     │
     ├─► [retrieval_node]
     │       ├─ asyncio.gather → parallel retrieval per sub-question
     │       │       └─ retrieval_agent.ainvoke → retrieval_tool.ainvoke(query)
     │       │               └─ retrieve(query, k=4) → Pinecone similarity_search
     │       │                       └─ OpenAI text-embedding-3-small → vector search
     │       ├─ serialize_chunks(docs) → "Chunk N (page=X): ..."
     │       └─ Updates state: context
     │
     ├─► [summarization_node]
     │       ├─ LLM call: gpt-4o-mini with question + context
     │       └─ Updates state: draft_answer
     │
     └─► [verification_node]
             ├─ LLM call: gpt-4o-mini with question + context + draft_answer
             └─ Updates state: answer
     │
     ▼
[QAResponse(answer=..., context=...)]
     │
     ▼
HTTP 200 Response to client
```

---

## License

This project is part of the **IKMS (Intelligent Knowledge Management System)** academic project.

---

*Built with using FastAPI, LangGraph, Pinecone, and OpenAI.*
