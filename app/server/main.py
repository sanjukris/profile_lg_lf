from __future__ import annotations
from typing import List, Optional, Dict, Any
import re

from fastapi import FastAPI
from pydantic import BaseModel

# ✅ import the ASYNC function
from app.agents.profile_agent import handle_request_async

app = FastAPI(title="Profile Agent A2A", version="0.1.0")

class TextPart(BaseModel):
    kind: str = "text"
    text: Optional[str] = None

class Message(BaseModel):
    kind: str = "message"
    role: str
    parts: List[TextPart]

def _extract_member_id(text: str) -> str:
    m = re.search(r"\b(\d{6,})\b", text or "")
    return m.group(1) if m else "378477398"

def _first_text(parts: List[TextPart]) -> str:
    for p in parts or []:
        if p.kind == "text" and p.text:
            return p.text
    return ""

@app.get("/healthz")
async def healthz() -> Dict[str, Any]:
    return {"ok": True}

@app.get("/a2a/agent-card")
async def agent_card() -> Dict[str, Any]:
    return {
        "kind": "agent_card",
        "name": "profile-agent",
        "description": "Profile Agent with mocked APIs. Returns profile overview or preferences as structured JSON.",
        "version": "0.1.0",
        "capabilities": {"streaming": False},
        "inputs": [{"kind": "message"}],
        "outputs": [{"kind": "message"}],
    }

@app.post("/a2a/messages")
async def a2a_messages(msg: Message) -> Dict[str, Any]:
    text = _first_text(msg.parts)
    member_id = _extract_member_id(text)

    # ✅ await the async handler (DO NOT call the sync wrapper here)
    tool_name, payload = await handle_request_async(query=text, member_id=member_id)

    return {
        "kind": "message",
        "role": "assistant",
        "parts": [
            {"kind": "text", "text": tool_name},
            {"kind": "json", "json": payload},
        ],
    }
