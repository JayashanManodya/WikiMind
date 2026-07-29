# IKMS RAG Agent System

**Entity Type**: `SYSTEM`  
**Last Updated**: `2026-07-29`

## Information from Uploaded Sources

### Document Provenance
- Mentioned in: [README.md](file://README.md)

### Overview
The IKMS RAG Agent System is a backend service that implements a multi-agent Retrieval-Augmented Generation (RAG) pipeline for intelligent document question-answering. It allows users to upload PDF documents to be indexed into a Pinecone vector store and ask natural language questions about those documents, receiving verified answers through a structured agentic process.

### Known Facts & Data
- The system processes PDFs entirely in-memory with no disk writes. (Provenance: Project Overview)
- The multi-agent pipeline consists of four stages: Planning, Retrieval, Summarization, and Verification. (Provenance: 5.2 Multi-Agent Pipeline)

## Related Entities
[[FastAPI]], [[LangGraph]], [[OpenAI]], [[Pinecone]], [[Retrieval-Augmented Generation (RAG)]]

## Knowledge Graph Relationships
- [[IKMS RAG Agent System]] --[`CATEGORIZED_AS`]--> [[Retrieval-Augmented Generation (RAG)]]
- [[IKMS RAG Agent System]] --[`USES_TECHNOLOGY`]--> [[FastAPI]]
- [[IKMS RAG Agent System]] --[`USES_TECHNOLOGY`]--> [[Pinecone]]
- [[IKMS RAG Agent System]] --[`USES_TECHNOLOGY`]--> [[OpenAI]]
- [[IKMS RAG Agent System]] --[`USES_TECHNOLOGY`]--> [[LangGraph]]

## Backlinks
- [[FastAPI]]
- [[LangGraph]]
- [[OpenAI]]
- [[Pinecone]]
- [[Retrieval-Augmented Generation (RAG)]]
## Document Sources
- [README.md](file://README.md)
