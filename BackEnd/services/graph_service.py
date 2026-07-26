from typing import Dict, Any, Optional, List
from typing_extensions import TypedDict
from pathlib import Path

from langgraph.graph import StateGraph, END

from BackEnd.schemas import FullPipelineResponse, QAResponse
from BackEnd.services.parser_service import parser_service
from BackEnd.services.cleaner_service import cleaner_service
from BackEnd.services.knowledge_service import knowledge_service
from BackEnd.services.wiki_service import wiki_service
from BackEnd.services.vector_service import vector_service
from BackEnd.services.retriever_service import retriever_service

# --- State Definitions ---

class IngestionState(TypedDict, total=False):
    file_id: str
    filename: str
    total_pages: int
    entities_count: int
    wiki_pages_count: int
    vector_indexed: bool
    status: str
    error_message: Optional[str]

class QAState(TypedDict, total=False):
    question: str
    top_k: int
    max_chars: int
    assembled_context: str
    qa_response: Optional[Dict[str, Any]]
    status: str
    error_message: Optional[str]


class LangGraphEngine:
    def __init__(self):
        self.ingestion_graph = self._build_ingestion_graph()
        self.qa_graph = self._build_qa_graph()

    # --- Ingestion Graph Builder ---

    def _build_ingestion_graph(self):
        workflow = StateGraph(IngestionState)

        # 1. Define Nodes
        def parse_node(state: IngestionState) -> Dict[str, Any]:
            try:
                res = parser_service.parse_document(state["file_id"])
                return {"filename": res.original_filename, "total_pages": res.total_pages, "status": "parsed"}
            except Exception as e:
                return {"status": "error", "error_message": f"Parsing failed: {str(e)}"}

        def clean_node(state: IngestionState) -> Dict[str, Any]:
            if state.get("status") == "error":
                return {}
            try:
                cleaner_service.clean_document(state["file_id"])
                return {"status": "cleaned"}
            except Exception as e:
                return {"status": "error", "error_message": f"Cleaning failed: {str(e)}"}

        def extract_node(state: IngestionState) -> Dict[str, Any]:
            if state.get("status") == "error":
                return {}
            try:
                res = knowledge_service.extract_knowledge_for_document(state["file_id"])
                return {"entities_count": len(res.entities), "status": "extracted"}
            except Exception as e:
                return {"status": "error", "error_message": f"Knowledge extraction failed: {str(e)}"}

        def wiki_node(state: IngestionState) -> Dict[str, Any]:
            if state.get("status") == "error":
                return {}
            try:
                res = wiki_service.generate_wiki_for_document(state["file_id"])
                return {"wiki_pages_count": res.total_pages_generated, "status": "wiki_generated"}
            except Exception as e:
                return {"status": "error", "error_message": f"Wiki generation failed: {str(e)}"}

        def embed_node(state: IngestionState) -> Dict[str, Any]:
            if state.get("status") == "error":
                return {}
            try:
                vector_service.index_all_wiki_pages()
                return {"vector_indexed": True, "status": "fully_processed"}
            except Exception as e:
                return {"status": "error", "error_message": f"Vector embedding failed: {str(e)}"}

        def error_recovery_node(state: IngestionState) -> Dict[str, Any]:
            return {"status": "recovered_with_error", "vector_indexed": False}

        # Add Nodes to Graph
        workflow.add_node("parse_node", parse_node)
        workflow.add_node("clean_node", clean_node)
        workflow.add_node("extract_node", extract_node)
        workflow.add_node("wiki_node", wiki_node)
        workflow.add_node("embed_node", embed_node)
        workflow.add_node("error_recovery_node", error_recovery_node)

        # 2. Define Routing Logic
        def route_after_parse(state: IngestionState) -> str:
            return "error_recovery_node" if state.get("status") == "error" else "clean_node"

        def route_after_clean(state: IngestionState) -> str:
            return "error_recovery_node" if state.get("status") == "error" else "extract_node"

        def route_after_extract(state: IngestionState) -> str:
            return "error_recovery_node" if state.get("status") == "error" else "wiki_node"

        def route_after_wiki(state: IngestionState) -> str:
            return "error_recovery_node" if state.get("status") == "error" else "embed_node"

        # Set Graph Edges
        workflow.set_entry_point("parse_node")
        workflow.add_conditional_edges("parse_node", route_after_parse)
        workflow.add_conditional_edges("clean_node", route_after_clean)
        workflow.add_conditional_edges("extract_node", route_after_extract)
        workflow.add_conditional_edges("wiki_node", route_after_wiki)
        workflow.add_edge("embed_node", END)
        workflow.add_edge("error_recovery_node", END)

        return workflow.compile()

    # --- QA Graph Builder ---

    def _build_qa_graph(self):
        workflow = StateGraph(QAState)

        # 1. Define Nodes
        def retrieve_node(state: QAState) -> Dict[str, Any]:
            try:
                top_k = state.get("top_k", 3)
                max_chars = state.get("max_chars", 4000)
                res = retriever_service.retrieve_multi_hop_context(
                    question=state["question"],
                    top_k=top_k,
                    max_chars=max_chars
                )
                return {"assembled_context": res.assembled_context, "status": "retrieved"}
            except Exception as e:
                return {"status": "error", "error_message": str(e)}

        def llm_qa_node(state: QAState) -> Dict[str, Any]:
            if state.get("status") == "error":
                return {}
            from BackEnd.services.qa_service import qa_service
            res = qa_service.answer_question(
                question=state["question"],
                top_k=state.get("top_k", 3),
                max_chars=state.get("max_chars", 4000)
            )
            return {"qa_response": res.model_dump(), "status": "answered"}

        workflow.add_node("retrieve_node", retrieve_node)
        workflow.add_node("llm_qa_node", llm_qa_node)

        workflow.set_entry_point("retrieve_node")
        workflow.add_edge("retrieve_node", "llm_qa_node")
        workflow.add_edge("llm_qa_node", END)

        return workflow.compile()

    # --- Execution Triggers ---

    def run_ingestion_graph(self, file_id: str) -> FullPipelineResponse:
        """Invokes the compiled LangGraph Document Ingestion StateGraph"""
        initial_state: IngestionState = {"file_id": file_id, "status": "initiated"}
        final_state = self.ingestion_graph.invoke(initial_state)

        filename = final_state.get("filename", "document.pdf")
        total_pages = final_state.get("total_pages", 1)
        entities_count = final_state.get("entities_count", 0)
        wiki_count = final_state.get("wiki_pages_count", 0)
        vector_indexed = final_state.get("vector_indexed", False)

        return FullPipelineResponse(
            file_id=file_id,
            filename=filename,
            total_pages=total_pages,
            entities_extracted=entities_count,
            wiki_pages_generated=wiki_count,
            vector_indexed=vector_indexed,
            status=final_state.get("status", "fully_processed"),
            message=f"LangGraph Ingestion Workflow executed successfully for '{filename}' across all nodes."
        )

    def run_qa_graph(self, question: str, top_k: int = 3, max_chars: int = 4000) -> QAResponse:
        """Invokes the compiled LangGraph QA StateGraph"""
        initial_state: QAState = {"question": question, "top_k": top_k, "max_chars": max_chars}
        final_state = self.qa_graph.invoke(initial_state)

        resp_dict = final_state.get("qa_response")
        if resp_dict:
            return QAResponse(**resp_dict)
        
        from BackEnd.services.qa_service import qa_service
        return qa_service.answer_question_deterministic(question, retriever_service.retrieve_multi_hop_context(question))

# Default singleton instance
graph_service = LangGraphEngine()
