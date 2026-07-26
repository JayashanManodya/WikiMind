import pytest
from langchain_core.prompts import ChatPromptTemplate
from BackEnd.services.langchain_service import langchain_engine

def test_langchain_engine_initialization():
    """Verify LangChainEngine initializes ChatPromptTemplate primitives"""
    assert isinstance(langchain_engine.extraction_prompt, ChatPromptTemplate)
    assert isinstance(langchain_engine.qa_prompt, ChatPromptTemplate)

def test_langchain_extraction_chain_execution():
    """Verify extract_knowledge_chain produces structured dict output with entities and relationships"""
    text = "Tesla is an EV manufacturer founded by Elon Musk in 2003."
    res = langchain_engine.extract_knowledge_chain(text)
    
    assert isinstance(res, dict)
    assert "entities" in res
    assert "relationships" in res
    assert any(e["name"] == "Tesla" for e in res["entities"])

def test_langchain_qa_chain_integration():
    """Verify QA chain integration with qa_service"""
    from BackEnd.services.qa_service import qa_service
    res = qa_service.answer_question("Who founded Tesla?")
    assert res.grounded is True
    assert "elon musk" in res.answer.lower()
