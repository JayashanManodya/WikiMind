# 📚 WikiMind — AI-Powered Knowledge Management Platform

WikiMind is an AI-powered Knowledge Management Platform that converts raw documents (PDFs, DOCX, TXT) into a structured, interlinked knowledge base similar to Wikipedia, enabling higher-quality Q&A and multi-hop reasoning over complex documentation.

---

## 🏗️ Project Architecture Overview

```
Upload Document ──► Parse ──► Knowledge Extraction ──► Wiki Generation ──► Storage (.md)
                                                                               │
Answer ◄── LLM ◄── Hybrid Retriever (Vector Search + Link Traversal) ◄── Vector Embeddings
```

---

## 📁 Repository Structure

```
WikiMind/
├── backend/            # FastAPI backend API service
│   └── main.py         # FastAPI application entry point
├── frontend/           # Web UI frontend (Vite/React)
├── docs/               # Technical documentation & project specifications
├── wiki/               # Generated Markdown Knowledge Base pages
├── storage/            # Local data persistence & ChromaDB vector store
├── tests/              # Unit and integration test suites
├── .env.example        # Environment variable template
├── .env                # Local environment configuration (git-ignored)
├── .gitignore          # Git exclusion rules
├── requirements.txt    # Frozen Python dependencies
└── README.md           # Project guide & roadmap documentation
```

---

## ⚡ Getting Started

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Setup Virtual Environment
```bash
# Windows
py -m venv .venv
.\.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and configure your API keys:
```bash
cp .env.example .env
```

### 5. Run the Backend API
```bash
python -m uvicorn backend.main:app --reload --port 8000
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to view the interactive FastAPI Swagger documentation.

---

## 🗺️ Engineering Roadmap

- [x] **Phase 1**: Project Architecture & Mental Model
- [x] **Phase 2**: Development Environment & Foundation
- [ ] **Phase 3**: Document Ingestion & Parsing
- [ ] **Phase 4**: Knowledge Extraction & Graph Builder
- [ ] **Phase 5**: Wiki Generation & Markdown Storage
- [ ] **Phase 6**: Hybrid Retrieval Engine (ChromaDB + Links)
- [ ] **Phase 7**: End-to-End LLM QA Pipeline
- [ ] **Phase 8**: Frontend Web Application
