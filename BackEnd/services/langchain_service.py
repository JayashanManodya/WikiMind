import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from BackEnd.schemas import KnowledgeExtractionResponse, QAResponse
from BackEnd.prompts import EXTRACTION_CHAT_PROMPT, QA_CHAT_PROMPT

class LangChainEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        # Centralized LangChain Prompt Templates
        self.extraction_prompt = EXTRACTION_CHAT_PROMPT
        self.qa_prompt = QA_CHAT_PROMPT

    def get_llm(self) -> Optional[ChatOpenAI]:
        """Returns initialized ChatOpenAI LLM instance if API key is present"""
        if not self.api_key:
            return None
        return ChatOpenAI(model=self.model_name, temperature=0.0, api_key=self.api_key)

    def extract_knowledge_chain(self, text: str) -> Dict[str, Any]:
        """Executes LangChain LCEL Chain (prompt | llm | parser) for Knowledge Extraction"""
        llm = self.get_llm()
        if not llm:
            from BackEnd.services.llm_service import llm_service
            return llm_service.extract_knowledge_deterministic(text)

        try:
            # Construct LCEL Chain with JsonOutputParser
            chain = self.extraction_prompt | llm | JsonOutputParser()
            return chain.invoke({"text": text})
        except Exception:
            from BackEnd.services.llm_service import llm_service
            return llm_service.extract_knowledge_deterministic(text)

    def answer_question_chain(self, question: str, context: str) -> Optional[QAResponse]:
        """Executes LangChain LCEL Chain with Pydantic Structured Output for Grounded QA"""
        llm = self.get_llm()
        if not llm:
            return None

        try:
            # Bind Pydantic QAResponse schema for structured output
            structured_llm = llm.with_structured_output(QAResponse)
            chain = self.qa_prompt | structured_llm
            result: QAResponse = chain.invoke({"question": question, "context": context})
            return result
        except Exception:
            return None

# Default singleton instance
langchain_engine = LangChainEngine()
