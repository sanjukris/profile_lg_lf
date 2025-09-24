from __future__ import annotations
from typing import Any, Dict, Tuple
from typing_extensions import TypedDict
import os, time
from pydantic import ValidationError

# LangGraph / LangChain OpenAI (model configured but not used in the hot path)
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI  # uses OpenAI SDK under the hood
# Docs (reference only): https://python.langchain.com/docs/integrations/chat/openai/  # noqa

from app.telemetry.tracing import get_current_trace
from app.utils.intent import classify_intent
from app.utils.json_utils import unwrap_tool_result
from app.utils.builders import build_email_address_output, build_preferences_output
from app.tools.profile_tools import fetch_email_and_address, fetch_contact_preference

# ------------------ LLM (OpenAI o4-mini) ------------------
# You can flip USE_LLM_SUMMARY=1 later to add an LLM summarization node.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o4-mini")  # official model page: https://platform.openai.com/docs/models/o4-mini
# llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)  # requires OPENAI_API_KEY
# ----------------------------------------------------------

# ------------------ LangGraph State -----------------------
class AgentState(TypedDict, total=False):
    query: str
    member_id: str
    intent: str
    raw: Dict[str, Any]
    out: Dict[str, Any]

def node_classify(state: AgentState) -> AgentState:
    client = get_current_trace()
    span = client.start_span(name="lg.classify") if client else None
    intent = classify_intent(state.get("query", ""))
    if span: span.update(output={"intent": intent}); span.end()
    return {**state, "intent": intent}

def node_fetch(state: AgentState) -> AgentState:
    client = get_current_trace()
    span = client.start_span(name="lg.fetch", input={"intent": state.get("intent")}) if client else None
    t0 = time.perf_counter()
    intent = state.get("intent")
    member_id = state.get("member_id", "")
    if intent == "fetch_email_and_address":
        raw = fetch_email_and_address(member_id=member_id)
    else:
        raw = fetch_contact_preference(member_id=member_id)
    t1 = time.perf_counter()
    raw = unwrap_tool_result(raw)  # pass-through now, but harmless
    if span: span.update(output={"ms": round((t1 - t0)*1000, 1), "keys": list(raw.keys())}); span.end()
    return {**state, "raw": raw}

def node_build(state: AgentState) -> AgentState:
    client = get_current_trace()
    span = client.start_span(name="lg.build", input={"intent": state.get("intent")}) if client else None
    t0 = time.perf_counter()
    member_id = state.get("member_id", "")
    intent = state.get("intent")
    raw = state.get("raw") or {}
    if intent == "fetch_email_and_address":
        out = build_email_address_output(member_id, raw.get("email_json"), raw.get("address_json")).model_dump()
    else:
        out = build_preferences_output(member_id, raw.get("preferences_json")).model_dump()
    t1 = time.perf_counter()
    if span: span.update(output={"ms": round((t1 - t0)*1000, 1)}); span.end()
    return {**state, "out": out}
# ----------------------------------------------------------

# Build the LangGraph once
_graph = StateGraph(AgentState)
_graph.add_node("classify", node_classify)
_graph.add_node("fetch", node_fetch)
_graph.add_node("build", node_build)
_graph.set_entry_point("classify")
_graph.add_edge("classify", "fetch")
_graph.add_edge("fetch", "build")
_graph.add_edge("build", END)
app_graph = _graph.compile()

def handle_request(*, query: str, member_id: str) -> Tuple[str, Dict[str, Any]]:
    """
    Routes the query through a small LangGraph (classify -> fetch -> build),
    emits Langfuse spans (if configured), prints timings,
    and returns (intent, structured_dict) just like before.
    """
    client = get_current_trace()
    span_outer = client.start_span(name="handle_request", input={"query": query, "member_id": member_id}) if client else None

    t0 = time.perf_counter()
    state: AgentState = {"query": query, "member_id": member_id}
    result: AgentState = app_graph.invoke(state)
    t1 = time.perf_counter()

    intent = result.get("intent", "")
    out = result.get("out", {})

    print(
        f"[timing] handle_request[{intent} via LangGraph]: total={(t1 - t0)*1000:.1f} ms"
    )
    if span_outer:
        try: span_outer.end(output={"intent": intent, "total_ms": round((t1 - t0)*1000, 1)})
        except Exception: pass
    return intent, out
