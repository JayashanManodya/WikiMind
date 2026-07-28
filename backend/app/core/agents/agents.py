"""Agent implementations for the multi-agent RAG flow.

This module defines agents (Planning, Retrieval, Summarization, Verification)
and node functions that LangGraph uses to invoke them.
"""

import asyncio
from typing import List

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage

from ..llm.factory import create_chat_model
from .prompts import (
    RETRIEVAL_SYSTEM_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    PLANNING_AGENT_PROMPT,
)
from .state import QAState
from .tools import retrieval_tool


def _extract_last_ai_content(messages: List[object]) -> str:
    """Extract the content of the last AIMessage in a messages list."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return str(msg.content)
    return ""

def create_agent(model, tools, system_prompt):
    """Wrapper to maintain the user's preferred coding structure while ensuring functionality."""
    if tools:
        model = model.bind_tools(tools)
    
    async def ainvoke(self, input_data, config=None, **kwargs):
        # input_data can be a string (question) or a dict with messages
        if isinstance(input_data, str):
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=input_data)]
        else:
            # Handle standard LangChain dict input if needed
            msgs = input_data.get("messages", [])
            messages = [SystemMessage(content=system_prompt)] + msgs
            
        result = await model.ainvoke(messages, config=config, **kwargs)
        return {"messages": messages + [result]}

    def invoke(self, input_data, config=None, **kwargs):
        if isinstance(input_data, str):
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=input_data)]
        else:
            msgs = input_data.get("messages", [])
            messages = [SystemMessage(content=system_prompt)] + msgs
            
        result = model.invoke(messages, config=config, **kwargs)
        return {"messages": messages + [result]}
    
    return type("Agent", (), {"invoke": invoke, "ainvoke": ainvoke})()


# Define agents at module level for reuse

planning_agent = create_agent(
    model=create_chat_model(),
    tools=[],
    system_prompt=PLANNING_AGENT_PROMPT,
)

retrieval_agent = create_agent(
    model=create_chat_model(),
    tools=[retrieval_tool],
    system_prompt=RETRIEVAL_SYSTEM_PROMPT,
)

summarization_agent = create_agent(
    model=create_chat_model(),
    tools=[],
    system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
)

verification_agent = create_agent(
    model=create_chat_model(),
    tools=[],
    system_prompt=VERIFICATION_SYSTEM_PROMPT,
)

def planning_node(state: QAState) -> QAState:
    """Planning Agent node: detects ambiguity and generates sub-questions."""
    question = state["question"]
    
    result = planning_agent.invoke(question)
    content = _extract_last_ai_content(result["messages"])
    
    # Parsing logic for plan and sub-questions
    plan = ""
    sub_questions = []
    
    if "Plan:" in content:
        parts = content.split("Plan:")
        if len(parts) > 1:
            plan_part = parts[1].split("Sub-questions:")[0].strip()
            plan = plan_part
    
    if "Sub-questions:" in content:
        parts = content.split("Sub-questions:")
        if len(parts) > 1:
            sub_q_part = parts[1].strip()
            sub_questions = [q.strip("- ").strip() for q in sub_q_part.split("\n") if q.strip()]

    return {
        "plan": plan,
        "sub_questions": sub_questions if sub_questions else [question]
    }


async def retrieval_node(state: QAState) -> QAState:
    """Retrieval Agent node: gathers context from vector store using sub-questions (parallellized)."""
    sub_questions = state.get("sub_questions") or [state["question"]]
    
    async def process_question(q):
        result = await retrieval_agent.ainvoke({"messages": [HumanMessage(content=f"Retrieve context for: {q}")]})
        
        last_msg = result["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            tool_tasks = []
            for tool_call in last_msg.tool_calls:
                if tool_call["name"] == "retrieval_tool":
                    # retrieval_tool.ainvoke returns (content, artifact)
                    tool_tasks.append(retrieval_tool.ainvoke(tool_call["args"]))
            
            if tool_tasks:
                tool_results = await asyncio.gather(*tool_tasks)
                # If tool returns (content, artifact), res[0] is content. 
                # If tool returns just content (string), res is content.
                final_contents = []
                for res in tool_results:
                    if isinstance(res, (tuple, list)) and len(res) > 0:
                        final_contents.append(res[0])
                    else:
                        final_contents.append(res)
                return final_contents
        return []

    # Run all sub-questions in parallel
    results = await asyncio.gather(*(process_question(q) for q in sub_questions))
    
    # Flatten results and join
    all_context = [ctx for sublist in results for ctx in sublist]
                    
    return {
        "context": "\n\n".join(all_context) if all_context else "No context found.",
    }


def summarization_node(state: QAState) -> QAState:
    """Summarization Agent node: generates draft answer from context."""
    question = state["question"]
    context = state.get("context")

    user_content = f"Question: {question}\n\nContext:\n{context}"

    result = summarization_agent.invoke({"messages": [HumanMessage(content=user_content)]})
    draft_answer = _extract_last_ai_content(result["messages"])

    return {
        "draft_answer": draft_answer,
    }


def verification_node(state: QAState) -> QAState:
    """Verification Agent node: verifies and corrects the draft answer."""
    question = state["question"]
    context = state.get("context", "")
    draft_answer = state.get("draft_answer", "")

    user_content = f"""Question: {question}

Context:
{context}

Draft Answer:
{draft_answer}

Please verify and correct the draft answer, removing any unsupported claims."""

    result = verification_agent.invoke({"messages": [HumanMessage(content=user_content)]})
    answer = _extract_last_ai_content(result["messages"])

    return {
        "answer": answer,
    }
