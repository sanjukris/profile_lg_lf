from __future__ import annotations
import os, re, json
from typing import Optional

from app.utils.intent_keywords import classify_intent_keywords

_ALLOWED = {"fetch_email_and_address", "fetch_contact_preference"}

_SYSTEM_PROMPT = """\
You are a router. Classify the user's request into exactly one of:
- fetch_email_and_address
- fetch_contact_preference

Rules:
- Return ONLY the matching identifier above.
- Do not include extra words or explanation.
"""

def _parse_intent(text: str) -> Optional[str]:
    if not text:
        return None
    # try strict JSON first
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            v = str(obj.get("intent", "")).strip()
            if v in _ALLOWED:
                return v
    except Exception:
        pass
    # then regex for the allowed tokens
    m = re.search(r"(fetch_email_and_address|fetch_contact_preference)", text, re.I)
    if m:
        val = m.group(1).lower()
        return val if val in _ALLOWED else None
    return None

# ---------------------------
# LangGraph / OpenAI (o4-mini)
# ---------------------------
def _classify_with_openai(query: str) -> Optional[str]:
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
    except Exception as e:
        print(f"[intent-llm] openai stack import failed: {e}")
        return None

    model = os.getenv("OPENAI_MODEL", "o4-mini")
    try:
        llm = ChatOpenAI(model=model)
        resp = llm.invoke([SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=query or "")])
        text = (getattr(resp, "content", None) or "").strip()
        intent = _parse_intent(text)
        if not intent:
            # Second try: instruct JSON
            resp = llm.invoke(
                [SystemMessage(content=_SYSTEM_PROMPT + "\nReturn JSON: {\"intent\":\"...\"} exactly."),
                 HumanMessage(content=query or "")]
            )
            text = (getattr(resp, "content", None) or "").strip()
            intent = _parse_intent(text)
            print(f"[intent-llm] openai classify: intent={intent}")
        return intent
    except Exception as e:
        print(f"[intent-llm] openai classify failed: {e}")
        return None

#
def classify_intent_llm(query: str) -> str:
    """
    Orchestrates which LLM stack to use based on INTENT_LLM_STACK.
    Falls back to keywords if anything fails.
    """
    intent = _classify_with_openai(query)
    print(f"[intent-llm] openai classify: intent={intent}")
    return intent or classify_intent_keywords(query)
