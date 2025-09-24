from __future__ import annotations
import os
import time
import asyncio
from typing import Any, Dict

# ------------------------------------------------------------------
# Config (mocks)
# ------------------------------------------------------------------
API_BASE = os.getenv("PROFILE_API_BASE", "https://uat.api.securecloud.tbd.com").rstrip("/")
API_KEY = os.getenv("PROFILE_API_KEY", "tbd")
BASIC_AUTH = os.getenv("PROFILE_BASIC_AUTH", "tbd")
SCOPE = os.getenv("PROFILE_SCOPE", "public")
PREF_USERNM = os.getenv("PROFILE_USERNM", "test")

# Optional simulated latency (milliseconds). Default 0.
MOCK_DELAY_MS = int(os.getenv("MOCK_DELAY_MS", "0"))

async def _maybe_sleep() -> None:
    if MOCK_DELAY_MS > 0:
        await asyncio.sleep(MOCK_DELAY_MS / 1000.0)

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
# Async "HTTP" helpers (mocked)
# ------------------------------------------------------------------
async def _get_access_token_async() -> str:
    t0 = time.perf_counter()
    await _maybe_sleep()
    token = ACCESS["access_token"]
    print(f"[timing] access_token: {(time.perf_counter() - t0)*1000:.1f} ms")
    return token

async def _get_email_async(member_id: str, bearer: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    await _maybe_sleep()
    print(f"[timing] GET email(member_id={member_id}): {(time.perf_counter() - t0)*1000:.1f} ms")
    return EMAIL

async def _get_address_async(member_id: str, bearer: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    await _maybe_sleep()
    print(f"[timing] GET address(member_id={member_id}): {(time.perf_counter() - t0)*1000:.1f} ms")
    return ADDR

async def _get_preferences_async(member_id: str, bearer: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    await _maybe_sleep()
    print(f"[timing] GET preferences(member_id={member_id}): {(time.perf_counter() - t0)*1000:.1f} ms")
    return PREFS

# ------------------------------------------------------------------
# Public async tool-like functions (use asyncio.gather for concurrency)
# ------------------------------------------------------------------
async def fetch_email_and_address_async(*, member_id: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    token = await _get_access_token_async()
    t1 = time.perf_counter()
    start = time.perf_counter()
    email_json, address_json = await asyncio.gather(
        _get_email_async(member_id, token),
        _get_address_async(member_id, token),
    )
    t3 = time.perf_counter()
    print(
        "[timing] tool.fetch_email_and_address(async): "
        f"token={(t1 - t0)*1000:.1f} ms, "
        f"await_both={(t3 - start)*1000:.1f} ms, "
        f"total={(t3 - t0)*1000:.1f} ms"
    )
    return {"email_json": email_json, "address_json": address_json}

async def fetch_contact_preference_async(*, member_id: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    token = await _get_access_token_async()
    t1 = time.perf_counter()
    prefs = await _get_preferences_async(member_id, token)
    t2 = time.perf_counter()
    print(
        "[timing] tool.fetch_contact_preference(async): "
        f"token={(t1 - t0)*1000:.1f} ms, "
        f"prefs={(t2 - t1)*1000:.1f} ms, "
        f"total={(t2 - t0)*1000:.1f} ms"
    )
    return {"preferences_json": prefs}

# ------------------------------------------------------------------
# Backward-compatible sync wrappers (for run_demo.py and CLI use)
# ------------------------------------------------------------------
def _in_running_loop() -> bool:
    try:
        loop = asyncio.get_running_loop()
        return loop.is_running()
    except RuntimeError:
        return False

def fetch_email_and_address(*, member_id: str) -> Dict[str, Any]:
    if _in_running_loop():
        raise RuntimeError("Use: await fetch_email_and_address_async(...) inside async contexts")
    return asyncio.run(fetch_email_and_address_async(member_id=member_id))

def fetch_contact_preference(*, member_id: str) -> Dict[str, Any]:
    if _in_running_loop():
        raise RuntimeError("Use: await fetch_contact_preference_async(...) inside async contexts")
    return asyncio.run(fetch_contact_preference_async(member_id=member_id))
