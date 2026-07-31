# 🧠 WikiMind — AI-Powered Intelligent Knowledge Management Platform

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_Flow-FF6B6B?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![LangSmith](https://img.shields.io/badge/LangSmith-100%25_Accuracy-2A7FFF?style=flat-square)](https://smith.langchain.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev)
[![Turso DB](https://img.shields.io/badge/Turso_DB-libsql-00E599?style=flat-square&logo=sqlite&logoColor=black)](https://turso.tech)
[![Pinecone](https://img.shields.io/badge/Pinecone-VectorDB-000000?style=flat-square)](https://pinecone.io)
[![LlamaParse](https://img.shields.io/badge/LlamaParse-Document_AI-FF6B6B?style=flat-square)](https://llamaindex.ai)

**WikiMind** is a state-of-the-art, full-stack AI-Powered Intelligent Knowledge Management System (IKMS) that transforms unstructured documents into a structured, interlinked **Wikipedia-style Knowledge Base** and an **Interactive 2D Physics Knowledge Graph**. It features a **LangGraph StateGraph Agentic Flow**, **LangSmith 100% Accuracy Benchmark verification**, a **zero-hallucination grounded QA assistant** with click-through source citations, clean markdown rendering without asterisk clutter, and cross-device Turso Cloud Database connection pooling.

---

## 🌟 Key Features

- 📄 **Multi-Format Document Ingestion**: Support for **PDF, DOCX, XLSX, XLS, CSV, TXT, Markdown (.md), PPTX, and HTML** with layout and structured table extraction powered by LlamaParse & PyMuPDF.
- ⚡ **Single-Pass Ingestion Engine**: Merges Stage 4 Content Enrichment and Stage 5 Knowledge Extraction into **1 single LLM call**, cutting document upload processing latency by **50%**.
- 🤖 **LangGraph Agentic StateGraph**: State-driven execution pipeline (`START -> grounded_qa -> END`) with tool-calling capabilities (`retrieval_tool`) for multi-turn conversational follow-up reasoning.
- 🎯 **LangSmith Evaluated & Benchmark Verified**: Tested against the 20-question golden CV benchmark dataset (`Jayashan_Manodya_CV_Benchmark`), achieving **100.0% QA Correctness** and **100.0% Groundedness Score**.
- 💬 **Grounded Zero-Hallucination QA Assistant**: Fact-checked answers synthesized strictly from retrieved vector context with click-through source citations linking directly to wiki pages.
- 🎨 **Frontend Bold Markdown & Bullet Renderer**: Custom inline markdown parser (`renderFormattedMarkdown`) in `ChatPage.jsx` rendering `**bold**` text as clean HTML `<strong>` elements and bullets without raw asterisk clutter (`**`).
- ⏱️ **Instant Memory Caching & DB Connection Pooling**: React `DataContext` memory state caching and global Turso `libsql_client` connection pooling delivering **< 50ms instant chat loading and session switching**.
- 🖼️ **Viewport-Bounded Chat Card**: Locked viewport layout height (`calc(100vh - 110px)`) with internal message feed scrolling to prevent page stretching.
- 🌐 **Interactive 2D Physics Knowledge Graph**: Canvas simulation engine with node repulsion, line glow, zoom/pan controls, physics dynamics, and near-node popover preview dialogs.
- ☁️ **Turso Edge Cloud DB Persistence**: Cross-device synchronization for chat sessions, message history, wiki pages, and relationship graph edges.
- 🔒 **Google OAuth 2.0 & JWT Isolation**: Secure authentication with per-user data isolation and custom profile avatars.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   WikiMind Frontend UI                                  │
│       [ Overview ]   •   [ Chat ]   •   [ Upload ]   •   [ Knowledge Base ]  •  [ Guide ] │
└────────────────────────────┬────────────────────────────────────────────┘
                                             │ REST API / JSON
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                FastAPI Backend Engine                                   │
│  ┌────────────────────┐   ┌────────────────────────────────┐   ┌─────────────────────┐  │
│  │ LlamaParse & PyMu  │   │  LangGraph StateGraph Engine   │   │ Grounded QA Service │  │
│  │ Document Parser    │   │  (grounded_qa_agent + tool)    │   │ & Vector Retrieval  │  │
│  └─────────┬──────────┘   └───────────────┬────────────────┘   └──────────┬──────────┘  │
└────────────┼──────────────────────────────┼───────────────────────────────┼─────────────┘
             │                              │                               │
             ▼                              ▼                               ▼
┌────────────────────────┐┌───────────────────────────────────┐┌────────────────────────────┐
│  LlamaCloud API        ││  Turso Cloud Database             ││  Pinecone Vector Store     │
│  (Layout PDF Parser)   ││  (libsql SQLite Connection Pool)  ││  (1536-dim Text Embeddings)│
└────────────────────────┘└───────────────────────────────────┘└────────────────────────────┘
```

---

## 📁 Repository Directory Structure

```text
WikiMind/
├── backend/
│   ├── app/
│   │   ├── api.py                   # FastAPI routing, CORS middleware & REST endpoints
│   │   ├── models.py                # Pydantic request/response schemas
│   │   ├── services/
│   │   │   └── qa_service.py        # Grounded QA LLM answer & citation pipeline
│   │   └── core/
│   │       ├── config.py            # Pydantic Settings & environment manager
│   │       ├── db.py                # Turso Edge SQLite connection pooling & CRUD
│   │       ├── auth.py              # Google OAuth 2.0 token verification & JWT
│   │       ├── paths.py             # Central path manager & /tmp fallback for Vercel
│   │       ├── agents/
│   │       │   ├── agents.py        # Tool-calling grounded QA agent & node handlers
│   │       │   ├── graph.py         # LangGraph StateGraph workflow orchestrator
│   │       │   ├── prompts.py       # Master consolidated system prompt & formatting rules
│   │       │   └── tools.py         # Retrieval tool wrappers for LangGraph
│   │       ├── ingestion/
│   │       │   ├── parser.py        # Multi-format document parser (PDF, DOCX, XLSX, TXT)
│   │       │   ├── llama_parser.py  # LlamaParse OCR & layout extraction
│   │       │   ├── cleaner.py       # Stage 3 deterministic cleaning & normalization
│   │       │   ├── enricher.py      # Stage 4 content enrichment (0ms LLM reuse)
│   │       │   ├── extractor.py     # Stage 5 single-pass LLM knowledge extractor
│   │       │   └── wiki_generator.py# Structured 8-stage ingestion pipeline orchestrator
│   │       └── retrieval/
│   │           └── vector_store.py  # OpenAI embeddings & Pinecone indexing
│   ├── main.py                      # Uvicorn entry point
│   ├── pyproject.toml               # Python dependencies & Vercel builder config
│   └── .env                         # Backend environment variables
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx                 # React root entry point
│   │   ├── App.jsx                  # Main application gate & tab router
│   │   ├── index.css                # Global CSS design system, animations & media queries
│   │   ├── api/
│   │   │   └── client.js            # Axios REST client with Bearer auth token
│   │   ├── context/
│   │   │   ├── AuthContext.jsx      # Google OAuth session context
│   │   │   └── DataContext.jsx      # React Memory Cache store for 0ms tab switching
│   │   ├── components/
│   │   │   ├── Navbar.jsx           # Glassmorphic responsive top navigation bar
│   │   │   ├── HeroNodeGraph.jsx    # Interactive physics node graph canvas
│   │   │   ├── KnowledgeGraphCanvas.jsx # Full-featured 2D Knowledge Graph visualizer
│   │   │   ├── NodePopover.jsx      # Near-node popover preview dialog
│   │   │   ├── LoginModal.jsx       # Google Sign-In authentication modal
│   │   │   └── Footer.jsx           # Platform footer component
│   │   └── pages/
│   │       ├── DashboardPage.jsx    # Overview tab with hero bento grid & collection cards
│   │       ├── ChatPage.jsx         # Grounded QA Chat tab with inline markdown renderer & fixed height
│   │       ├── WikiPage.jsx         # Knowledge Base article reader & graph tab
│   │       ├── UploadPage.jsx       # 4-stage document ingestion pipeline tab
│   │       └── GuidePage.jsx        # User guide, 4-step workflow arrows & FAQs tab
│   ├── package.json                 # Frontend React dependencies
│   ├── vite.config.js               # Vite bundler configuration
│   └── .env                         # Frontend environment variables
│
├── scripts/
│   ├── eval_cv_dataset.py           # 20-question LangSmith benchmark evaluation script
│   └── eval_langsmith_dataset.py    # General LangSmith dataset benchmark script
├── pyproject.toml                   # Root Pyproject Vercel builder fallback config
├── vercel.json                      # Vercel deployment routing configuration
└── README.md                        # Project documentation
```

---

## 🛠️ Technology Stack

### Backend Services
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
- **Agentic Workflow**: [LangGraph](https://langchain-ai.github.io/langgraph/) & [LangChain](https://www.langchain.com/)
- **Evaluation & Telemetry**: [LangSmith](https://smith.langchain.com/)
- **Database**: [Turso Edge SQLite](https://turso.tech) via `libsql-client` with Connection Pooling
- **Vector DB**: [Pinecone](https://www.pinecone.io/) (`text-embedding-3-small` OpenAI embeddings)
- **Parser**: [LlamaParse](https://llamaindex.ai/) + [PyMuPDF](https://pymupdf.readthedocs.io/)
- **LLM Engine**: [OpenAI GPT-4o-mini](https://platform.openai.com/)
- **Auth**: Google OAuth 2.0 Google ID Token Verification + PyJWT Bearer Tokens

### Frontend Services
- **Framework**: [React 18](https://reactjs.org/) + [Vite 5](https://vitejs.dev/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Styling**: Vanilla CSS Design System with HSL tokens, glassmorphic headers, smooth animations, and mobile breakpoints
- **HTTP Client**: [Axios](https://axios-http.com/)

---

## ⚡ Quick Start Guide

### 1. Prerequisites
- **Python**: `3.10+` (Python 3.12 recommended)
- **Node.js**: `v18+` & `npm`
- **uv**: `pip install uv` (recommended for fast Python environment management)

---

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Create environment configuration file
cp .env.example .env
```

#### Configure `backend/.env`:
```env
OPENAI_API_KEY=sk-proj-your_openai_api_key
OPENAI_MODEL_NAME=gpt-4o-mini
PINECONE_API_KEY=pcsk_your_pinecone_api_key
PINECONE_INDEX_NAME=wikimind
LLAMA_CLOUD_API_KEY=llx-your_llama_cloud_api_key

# LangSmith Tracing & Benchmarks
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=WikiMind-3Agent-Evaluation

# Database Settings (Turso Cloud SQLite)
TURSO_DATABASE_URL=libsql://wikimind-your_database.aws-us-west-2.turso.io
TURSO_AUTH_TOKEN=your_turso_jwt_auth_token

# Google OAuth Settings
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
JWT_SECRET_KEY=your_super_secret_jwt_key

# CORS Allowed Origins
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://wikimind.jayashan.online
```

#### Launch Backend Server:
```bash
# Start FastAPI backend with hot-reload
uv run main.py
```
Backend will be available at **`http://localhost:8000`** (Swagger API docs at `http://localhost:8000/docs`).

---

### 3. Frontend Setup

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Create frontend environment file
cp .env.example .env
```

#### Configure `frontend/.env`:
```env
VITE_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
VITE_API_BASE_URL=http://localhost:8000
```

#### Launch Frontend Dev Server:
```bash
# Start Vite development server
npm run dev
```
Frontend will be available at **`http://localhost:5173`**.

---

## 🧪 Benchmark Evaluation

Run the 20-question LangSmith benchmark evaluation suite:

```bash
.venv/Scripts/python scripts/eval_cv_dataset.py
```

### Evaluation Dashboard (LangSmith):
- **QA Correctness**: `1.0 (100.0%)`
- **Groundedness Score**: `1.0 (100.0%)`
- **Experiment URL**: [LangSmith Benchmark Dashboard](https://smith.langchain.com/)

---

## 📡 REST API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/auth/google` | Authenticate Google OAuth 2.0 credential & receive JWT access token |
| `GET` | `/auth/me` | Fetch authenticated user profile |
| `POST` | `/upload` | Ingest document (PDF, DOCX, XLSX, TXT, MD), extract entities & generate wiki pages |
| `POST` | `/qa` | Submit question to grounded QA engine & receive cited answer |
| `GET` | `/wiki/catalog` | List all generated wiki knowledge topic pages |
| `GET` | `/wiki/page/{name}` | Fetch full Markdown article content for a topic |
| `GET` | `/wiki/graph` | Fetch all Knowledge Graph nodes and relationship edges |
| `GET` | `/api/chat/sessions` | List user chat sessions from Turso DB |
| `GET` | `/api/chat/sessions/{id}/messages` | Fetch complete Q&A message history for a chat thread |
| `DELETE` | `/api/chat/sessions/{id}` | Delete a chat session from Turso DB |

---

## 👤 Author & License

- **Developer**: Jayashan Manodya ([@JayashanManodya](https://github.com/JayashanManodya))
- **Repository**: [WikiMind on GitHub](https://github.com/JayashanManodya/WikiMind)
- **License**: MIT License
