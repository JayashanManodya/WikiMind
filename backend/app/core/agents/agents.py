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

def _slice_latest_5(msgs: List[object]) -> List[object]:
    """Ensure only the latest 5 messages are passed to the LLM context window."""
    if len(msgs) <= 5:
        return msgs
    return msgs[-5:]


def create_agent(model, tools, system_prompt):
    """Wrapper to maintain state history while sending only the latest 5 messages to the LLM."""
    if tools:
        model = model.bind_tools(tools)
    
    async def ainvoke(self, input_data, config=None, **kwargs):
        if isinstance(input_data, str):
            msgs = [HumanMessage(content=input_data)]
        else:
            msgs = input_data.get("messages", [])
        
        recent_msgs = _slice_latest_5(msgs)
        messages = [SystemMessage(content=system_prompt)] + recent_msgs
            
        result = await model.ainvoke(messages, config=config, **kwargs)
        return {"messages": msgs + [result]}

    def invoke(self, input_data, config=None, **kwargs):
        if isinstance(input_data, str):
            msgs = [HumanMessage(content=input_data)]
        else:
            msgs = input_data.get("messages", [])
            
        recent_msgs = _slice_latest_5(msgs)
        messages = [SystemMessage(content=system_prompt)] + recent_msgs
            
        result = model.invoke(messages, config=config, **kwargs)
        return {"messages": msgs + [result]}
    
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

def _build_history_messages(state: QAState, current_prompt: str) -> List[object]:
    """Build full message history array from state and return accumulated messages."""
    history = state.get("history") or []
    msgs: List[object] = []
    
    for item in history:
        if isinstance(item, dict):
            role = item.get("role") or item.get("sender")
            text = item.get("text") or item.get("content") or ""
            if role in ["user", "human"]:
                msgs.append(HumanMessage(content=text))
            elif role in ["assistant", "bot", "ai"]:
                msgs.append(AIMessage(content=text))
        elif hasattr(item, "content"):
            msgs.append(item)
            
    msgs.append(HumanMessage(content=current_prompt))
    return msgs


def planning_node(state: QAState) -> QAState:
    """Planning Agent node: detects ambiguity and generates sub-questions."""
    question = state["question"]
    msgs = _build_history_messages(state, question)
    
    result = planning_agent.invoke({"messages": msgs})
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
    user_id = state.get("user_id") or "guest_user"
    
    async def process_question(q):
        msgs = _build_history_messages(state, f"Retrieve context for: {q}")
        result = await retrieval_agent.ainvoke({"messages": msgs})
        
        last_msg = result["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            tool_tasks = []
            for tool_call in last_msg.tool_calls:
                if tool_call["name"] == "retrieval_tool":
                    args = dict(tool_call["args"])
                    args["user_id"] = user_id
                    tool_tasks.append(retrieval_tool.ainvoke(args))
            
            if tool_tasks:
                tool_results = await asyncio.gather(*tool_tasks)
                final_contents = []
                for res in tool_results:
                    if isinstance(res, (tuple, list)) and len(res) > 0:
                        final_contents.append(res[0])
                    else:
                        final_contents.append(res)
                return final_contents

        # Direct retrieve fallback if tool_calls wasn't emitted by LLM
        from ..retrieval.vector_store import retrieve
        from ..retrieval.serialization import serialize_wikis
        docs = retrieve(q, k=3, user_id=user_id)
        if docs:
            return [serialize_wikis(docs)]

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
    msgs = _build_history_messages(state, user_content)

    result = summarization_agent.invoke({"messages": msgs})
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

    msgs = _build_history_messages(state, user_content)
    result = verification_agent.invoke({"messages": msgs})
    answer = _extract_last_ai_content(result["messages"])

    return {
        "answer": answer,
    }

