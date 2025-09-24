from __future__ import annotations
import os
import time
from typing import Any, Dict

from app.telemetry.tracing import get_current_trace

# ------------------------------------------------------------------
# Config (still here, though mocks don't use them)
# ------------------------------------------------------------------
API_BASE = os.getenv("PROFILE_API_BASE", "https://uat.api.securecloud.tbd.com").rstrip("/")
API_KEY = os.getenv("PROFILE_API_KEY", "tbd")
BASIC_AUTH = os.getenv("PROFILE_BASIC_AUTH", "tbd")
SCOPE = os.getenv("PROFILE_SCOPE", "public")
PREF_USERNM = os.getenv("PROFILE_USERNM", "test")

# Optional local delay for profiling (ms). Default 0.
MOCK_DELAY_MS = int(os.getenv("MOCK_DELAY_MS", "0"))

def _maybe_sleep():
    if MOCK_DELAY_MS > 0:
        # simulate network latency deterministically
        end = time.perf_counter() + (MOCK_DELAY_MS / 1000.0)
        while time.perf_counter() < end:
            pass

# ------------------------------------------------------------------
# Mock payloads
# ------------------------------------------------------------------
ACCESS = {"access_token": "tbd"}

EMAIL = {
    "email": [{
        "emailTypeCd": {"code": "EMAIL1", "name": "EMAIL 1", "desc": "EMAIL 1"},
        "emailUid": "1750954079330009717442120",
        "emailStatusCd": {"code": "BLANK", "name": "Blank", "desc": "..."},
        "emailAddress": "SAMPLEEMAILID_1@SAMPLEDOMAIN.COM",
    }]
}

ADDR = {
    "address": [{
        "addressTypeCd": {"code": "HOME", "name": "Home"},
        "addressLineOne": "1928288 DO NOT MAIL",
        "city": "AVON LAKE",
        "stateCd": {"code": "OH"},
        "countryCd": {"code": "US"},
        "countyCd": {"code": "093"},
        "zipCd": "44012",
        "addressUid": "1733664015649003100039610",
    }]
}

PREFS = {
    "memberPreference": [{
        "preferenceUid": "HRA",
        "preferenceTypeCd": {"code": "HRA", "name": "HRA Indicator"},
        "defaulted": "true",
        "clearSelection": "false",
        "allowClearSelection": "false",
        "terminationDt": "9999-12-31 00:00:00.000",
        "effectiveDt": None,
    }]
}

# ------------------------------------------------------------------
# Synchronous "HTTP" helpers (mocked)
# ------------------------------------------------------------------
def _get_access_token() -> str:
    client = get_current_trace()
    span = client.start_span(name="access_token") if client else None

    t0 = time.perf_counter()
    _maybe_sleep()
    token = ACCESS["access_token"]
    dt = (time.perf_counter() - t0) * 1000
    print(f"[timing] access_token: {dt:.1f} ms")

    if span:
        try:
            span.update(output={"status": "ok", "ms": round(dt, 1)})
            span.end()
        except Exception:
            pass

    return token


def _get_email(member_id: str, bearer: str) -> Dict[str, Any]:
    client = get_current_trace()
    span = client.start_span(name="get_email", input={"member_id": member_id}) if client else None

    t0 = time.perf_counter()
    _maybe_sleep()
    out = EMAIL
    dt = (time.perf_counter() - t0) * 1000
    print(f"[timing] GET email(member_id={member_id}): {dt:.1f} ms")

    if span:
        try:
            span.update(output={"status": "ok", "ms": round(dt, 1)})
            span.end()
        except Exception:
            pass
    return out


def _get_address(member_id: str, bearer: str) -> Dict[str, Any]:
    client = get_current_trace()
    span = client.start_span(name="get_address", input={"member_id": member_id}) if client else None

    t0 = time.perf_counter()
    _maybe_sleep()
    out = ADDR
    dt = (time.perf_counter() - t0) * 1000
    print(f"[timing] GET address(member_id={member_id}): {dt:.1f} ms")

    if span:
        try:
            span.update(output={"status": "ok", "ms": round(dt, 1)})
            span.end()
        except Exception:
            pass
    return out


def _get_preferences(member_id: str, bearer: str) -> Dict[str, Any]:
    client = get_current_trace()
    span = client.start_span(name="get_preferences", input={"member_id": member_id}) if client else None

    t0 = time.perf_counter()
    _maybe_sleep()
    out = PREFS
    dt = (time.perf_counter() - t0) * 1000
    print(f"[timing] GET preferences(member_id={member_id}): {dt:.1f} ms")

    if span:
        try:
            span.update(output={"status": "ok", "ms": round(dt, 1)})
            span.end()
        except Exception:
            pass
    return out

# ------------------------------------------------------------------
# Public tool-like functions (sync & event-loop safe)
# ------------------------------------------------------------------
def fetch_email_and_address(*, member_id: str) -> Dict[str, Any]:
    """
    Fetch the member's primary email and address (mocked).
    Synchronous & safe to call from inside an active asyncio loop.
    """
    client = get_current_trace()
    tool_span = client.start_span(name="tool.fetch_email_and_address", input={"member_id": member_id}) if client else None

    t0 = time.perf_counter()
    token = _get_access_token()
    t1 = time.perf_counter()
    email_json = _get_email(member_id, token)
    t2 = time.perf_counter()
    address_json = _get_address(member_id, token)
    t3 = time.perf_counter()

    print(
        "[timing] tool.fetch_email_and_address: "
        f"token={(t1 - t0)*1000:.1f} ms, "
        f"email={(t2 - t1)*1000:.1f} ms, "
        f"address={(t3 - t2)*1000:.1f} ms, "
        f"total={(t3 - t0)*1000:.1f} ms"
    )
    if tool_span:
        try:
            tool_span.update(output={"status": "ok", "ms": round((t3 - t0)*1000, 1)})
            tool_span.end()
        except Exception:
            pass

    return {"email_json": email_json, "address_json": address_json}


def fetch_contact_preference(*, member_id: str) -> Dict[str, Any]:
    """
    Fetch contact preferences for the member (mocked).
    Synchronous & safe to call from inside an active asyncio loop.
    """
    client = get_current_trace()
    tool_span = client.start_span(name="tool.fetch_contact_preference", input={"member_id": member_id}) if client else None

    t0 = time.perf_counter()
    token = _get_access_token()
    t1 = time.perf_counter()
    prefs = _get_preferences(member_id, token)
    t2 = time.perf_counter()

    print(
        "[timing] tool.fetch_contact_preference: "
        f"token={(t1 - t0)*1000:.1f} ms, "
        f"prefs={(t2 - t1)*1000:.1f} ms, "
        f"total={(t2 - t0)*1000:.1f} ms"
    )
    if tool_span:
        try:
            tool_span.update(output={"status": "ok", "ms": round((t2 - t0)*1000, 1)})
            tool_span.end()
        except Exception:
            pass

    return {"preferences_json": prefs}
