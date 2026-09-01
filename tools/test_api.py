#!/usr/bin/env python3
"""
Clarvyn API Manual Testing Tool
================================
Fires real requests at the running Clarvyn API service and prints
a human-readable inspection of every input and output.

Usage:
    python tools/test_api.py

Required environment variables (set in .env or shell):
    CLARVYN_API_URL  — base URL of the running service (e.g. http://localhost:8000)
    CLARVYN_API_KEY  — a provisioned API key (X-API-Key header)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Load .env manually — no third-party deps beyond httpx
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    """Read key=value pairs from .env in the project root (two levels up)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

_load_dotenv()

try:
    import httpx
except ImportError:
    print("ERROR: httpx is not installed. Run: pip install httpx")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_URL = os.environ.get("CLARVYN_API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.environ.get("CLARVYN_API_KEY", "")

REQUIRED_RESPONSE_FIELDS = [
    "risk_level",
    "summary",
    "clinical_explanation",
    "dental_implications",
    "recommendations",
    "alternative_medications",
    "confidence",
    "sources",
    "fallback",
]

TEST_PATIENT = {
    "patient": {
        "age": 62,
        "sex": "female",
        "conditions": ["hypertension", "type 2 diabetes"],
        "allergies": ["penicillin"],
    },
    "current_medications": [
        {"name": "Warfarin", "dosage": "5mg"},
        {"name": "Metformin", "dosage": "500mg"},
        {"name": "Lisinopril", "dosage": "10mg"},
    ],
    "candidate_medication": {
        "name": "Amoxicillin",
        "dosage": "500mg",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hr(char: str = "─", width: int = 60) -> None:
    print(char * width)

def _section(title: str) -> None:
    print()
    _hr("═")
    print(f"  {title}")
    _hr("═")

def _ok(msg: str) -> None:
    print(f"  ✅  {msg}")

def _fail(msg: str) -> None:
    print(f"  ❌  {msg}")

def _warn(msg: str) -> None:
    print(f"  ⚠️   {msg}")

def _info(msg: str) -> None:
    print(f"  ℹ️   {msg}")

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def check_health(client: httpx.Client) -> bool:
    _section("1 / Health Check")
    try:
        resp = client.get(f"{API_URL}/v1/health", timeout=5)
        if resp.status_code == 200 and resp.json().get("status") == "ok":
            _ok(f"Service is UP  ({API_URL}/v1/health → {resp.status_code})")
            return True
        else:
            _fail(f"Unexpected health response: {resp.status_code} — {resp.text}")
            return False
    except httpx.ConnectError:
        print()
        print(f"  ERROR: Could not connect to {API_URL} — is the server running?")
        print()
        print("  Start it with:")
        print(f"    cd Clarvyn && uvicorn main:app --reload --port 8000")
        return False
    except Exception as exc:
        _fail(f"Health check failed: {exc}")
        return False

# ---------------------------------------------------------------------------
# Analysis request
# ---------------------------------------------------------------------------

def run_analysis(client: httpx.Client) -> None:
    _section("2 / Analysis Request")

    if not API_KEY:
        print()
        print("  ERROR: CLARVYN_API_KEY is not set.")
        print("  Provision a key first:")
        print(f'    curl -s -X POST {API_URL}/v1/keys -H "X-Admin-Key: <your_admin_key>"')
        print("  Then set CLARVYN_API_KEY in your .env file.")
        return

    # Print request payload
    print()
    print("  Request payload:")
    _hr()
    print(json.dumps(TEST_PATIENT, indent=2))
    _hr()

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
    }

    print()
    print(f"  POST {API_URL}/v1/analyze")
    print(f"  X-API-Key: {API_KEY[:8]}{'*' * max(0, len(API_KEY) - 8)}")
    print()

    try:
        t0 = time.monotonic()
        resp = client.post(
            f"{API_URL}/v1/analyze",
            json=TEST_PATIENT,
            headers=headers,
            timeout=60,
        )
        elapsed_ms = int((time.monotonic() - t0) * 1000)
    except httpx.ConnectError:
        print(f"  ERROR: Could not connect to {API_URL} — is the server running?")
        return
    except httpx.TimeoutException:
        print("  ERROR: Request timed out after 60 seconds.")
        return
    except Exception as exc:
        print(f"  ERROR: Unexpected error — {exc}")
        return

    # Status + timing
    print(f"  HTTP Status : {resp.status_code}")
    print(f"  Response Time: {elapsed_ms} ms")

    # Handle auth failure
    if resp.status_code == 401:
        print()
        print("  ERROR: API key rejected — check CLARVYN_API_KEY in your .env")
        return

    # Handle other non-200
    if resp.status_code != 200:
        print()
        print(f"  ERROR: Unexpected status {resp.status_code}")
        print("  Response body:")
        _hr()
        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print(resp.text)
        _hr()
        return

    # Parse response
    try:
        data = resp.json()
    except Exception:
        print("  ERROR: Response is not valid JSON")
        print(resp.text)
        return

    # Print full response
    _section("3 / Full Response")
    print(json.dumps(data, indent=2))

    # Validate required fields
    _section("4 / Field Validation")
    all_pass = True
    for field in REQUIRED_RESPONSE_FIELDS:
        if field in data:
            _ok(f"{field}")
        else:
            _fail(f"{field}  ← MISSING")
            all_pass = False

    print()
    if all_pass:
        _ok("All required fields present — PASS")
    else:
        _fail("One or more required fields missing — FAIL")

    # Fallback warning
    if data.get("fallback") is True:
        print()
        _warn("WARNING: Service returned a fallback response. AI reasoning may have failed.")
        reason = data.get("fallback_reason")
        if reason:
            _info(f"Fallback reason: {reason}")

    # Summary
    _section("5 / Summary")
    _info(f"risk_level  : {data.get('risk_level', 'N/A')}")
    _info(f"confidence  : {data.get('confidence', 'N/A')}")
    _info(f"fallback    : {data.get('fallback', 'N/A')}")
    sources = data.get("sources", [])
    _info(f"sources     : {len(sources)} source(s) — {[s.get('name') for s in sources]}")
    summary = data.get("summary", "")
    if summary:
        print()
        print("  Summary:")
        for line in summary.split(". "):
            if line.strip():
                print(f"    {line.strip()}.")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("  Clarvyn API Test Tool")
    print(f"  Target: {API_URL}")

    with httpx.Client() as client:
        healthy = check_health(client)
        if not healthy:
            sys.exit(1)
        run_analysis(client)

    print()
    _hr("═")
    print("  Done.")
    _hr("═")
    print()

if __name__ == "__main__":
    main()
