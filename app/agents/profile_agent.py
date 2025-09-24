from __future__ import annotations
from typing import Any, Dict, Tuple
from typing_extensions import TypedDict
import asyncio
import time
from pydantic import ValidationError

from langgraph.graph import StateGraph, END

from app.utils.intent import classify_intent
from app.utils.json_utils import unwrap_tool_result
from app.utils.builders import build_email_address_output, build_preferences_output
from app.tools.profile_tools import (
    fetch_email_and_address_async,
    fetch_contact_preference_async,
)

# -------- LangGraph state --------
class AgentState(TypedDict, total=False):
    query: str
    member_id: str
    intent: str
    raw: Dict[str, Any]
    out: Dict[str, Any]

async def node_classify(state: AgentState) -> AgentState:
    intent = classify_intent(state.get("query", ""))
    return {**state, "intent": intent}

async def node_fetch(state: AgentState) -> AgentState:
    t0 = time.perf_counter()
    intent = state.get("intent")
    member_id = state.get("member_id", "")
    if intent == "fetch_email_and_address":
        raw = await fetch_email_and_address_async(member_id=member_id)
    else:
        raw = await fetch_contact_preference_async(member_id=member_id)
    raw = unwrap_tool_result(raw)
    print(f"[timing] node_fetch[{intent}]: {(time.perf_counter() - t0)*1000:.1f} ms")
    return {**state, "raw": raw}

async def node_build(state: AgentState) -> AgentState:
    t0 = time.perf_counter()
    member_id = state.get("member_id", "")
    intent = state.get("intent")
    raw = state.get("raw") or {}
    if intent == "fetch_email_and_address":
        out = build_email_address_output(member_id, raw.get("email_json"), raw.get("address_json")).model_dump()
    else:
        out = build_preferences_output(member_id, raw.get("preferences_json")).model_dump()
    print(f"[timing] node_build[{intent}]: {(time.perf_counter() - t0)*1000:.1f} ms")
    return {**state, "out": out}

_graph = StateGraph(AgentState)
_graph.add_node("classify", node_classify)
_graph.add_node("fetch", node_fetch)
_graph.add_node("build", node_build)
_graph.set_entry_point("classify")
_graph.add_edge("classify", "fetch")
_graph.add_edge("fetch", "build")
_graph.add_edge("build", END)
app_graph = _graph.compile()

# -------- Public API --------
async def handle_request_async(*, query: str, member_id: str) -> Tuple[str, Dict[str, Any]]:
    t0 = time.perf_counter()
    state: AgentState = {"query": query, "member_id": member_id}
    result: AgentState = await app_graph.ainvoke(state)
    intent = result.get("intent", "")
    out = result.get("out", {})
    print(f"[timing] handle_request[{intent} via LangGraph]: total={(time.perf_counter() - t0)*1000:.1f} ms")
    return intent, out

def handle_request(*, query: str, member_id: str) -> Tuple[str, Dict[str, Any]]:
    """
    Sync wrapper so existing scripts (run_demo.py) can call this directly.
    """
    return asyncio.run(handle_request_async(query=query, member_id=member_id))
