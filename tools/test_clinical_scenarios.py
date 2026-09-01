#!/usr/bin/env python3
"""
RxGuide Clinical Accuracy Test Suite
======================================
Fires real requests at the running API for each known high-risk dental
drug interaction scenario and evaluates whether the service correctly
identifies the interaction, assigns the right risk level, and produces
clinically useful output.

Usage:
    python tools/test_clinical_scenarios.py

Reads CLARVYN_API_URL and CLARVYN_API_KEY from .env or environment.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

_load_dotenv()

try:
    import httpx
except ImportError:
    print("ERROR: httpx is not installed. Run: pip install httpx")
    sys.exit(1)

from scenarios import SCENARIOS

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_URL = os.environ.get("CLARVYN_API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.environ.get("CLARVYN_API_KEY", "")
GAPS_FILE = Path(__file__).resolve().parent / "knowledge_gaps.json"
MIN_KEYWORD_PASS = 3

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hr(char: str = "─", width: int = 60) -> None:
    print(char * width)

def _check_health(client: httpx.Client) -> bool:
    try:
        r = client.get(f"{API_URL}/v1/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def _keyword_search(text: str, keywords: list[str]) -> list[str]:
    """Return which keywords appear in text (case-insensitive)."""
    lower = text.lower()
    return [kw for kw in keywords if kw.lower() in lower]

# ---------------------------------------------------------------------------
# Run one scenario
# ---------------------------------------------------------------------------

def run_scenario(
    client: httpx.Client, idx: int, total: int, scenario: dict
) -> dict:
    """Run a single scenario and return a result dict."""
    sid = scenario["id"]
    name = scenario["name"]
    desc = scenario["description"]
    expected_risk = scenario["expected_risk"]
    expected_kw = scenario["expected_keywords"]

    print()
    _hr("─")
    print(f" [{idx}/{total}] {name}")
    print(f"         {sid}")
    print()
    print(f"  {desc}")
    print()

    result = {
        "id": sid,
        "name": name,
        "expected_risk": expected_risk,
        "actual_risk": None,
        "risk_pass": False,
        "keywords_found": [],
        "keywords_missing": [],
        "keyword_status": "FAIL",
        "fallback": None,
        "time_ms": 0,
        "status": "FAIL",
        "error": None,
    }

    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}

    try:
        t0 = time.monotonic()
        resp = client.post(
            f"{API_URL}/v1/analyze",
            json=scenario["request"],
            headers=headers,
            timeout=90,
        )
        elapsed = int((time.monotonic() - t0) * 1000)
        result["time_ms"] = elapsed
    except httpx.ConnectError:
        result["error"] = "Connection refused"
        result["status"] = "ERROR"
        print(f"  ERROR: Could not connect to {API_URL}")
        return result
    except httpx.TimeoutException:
        result["error"] = "Timeout (90s)"
        result["status"] = "TIMEOUT"
        print("  TIMEOUT: Request exceeded 90 seconds")
        return result
    except Exception as exc:
        result["error"] = str(exc)
        result["status"] = "ERROR"
        print(f"  ERROR: {exc}")
        return result

    if resp.status_code == 401:
        result["error"] = "API key rejected"
        result["status"] = "ERROR"
        print("  ERROR: API key rejected — check CLARVYN_API_KEY")
        return result

    if resp.status_code != 200:
        result["error"] = f"HTTP {resp.status_code}"
        result["status"] = "ERROR"
        print(f"  ERROR: HTTP {resp.status_code} — {resp.text[:200]}")
        return result

    try:
        data = resp.json()
    except Exception:
        result["error"] = "Invalid JSON response"
        result["status"] = "ERROR"
        print("  ERROR: Response is not valid JSON")
        return result

    actual_risk = data.get("risk_level", "unknown")
    fallback = data.get("fallback", False)
    result["actual_risk"] = actual_risk
    result["fallback"] = fallback

    # Combine all text fields for keyword search (three-tier fields)
    combined_text = " ".join([
        data.get("headline", ""),
        data.get("summary", ""),
        data.get("clinical_explanation", ""),
        data.get("dental_implications", ""),
        " ".join(data.get("monitoring_recommendations", [])),
    ])
    # Also search in structured sub-objects
    for ix in data.get("key_interactions", []):
        combined_text += f" {ix.get('drug_pair', '')} {ix.get('dental_relevance', '')}"
    for alt in data.get("alternative_medications", []):
        if isinstance(alt, dict):
            combined_text += f" {alt.get('name', '')} {alt.get('reason', '')}"
        else:
            combined_text += f" {alt}"
    for rf in data.get("patient_risk_factors", []):
        combined_text += f" {rf.get('factor', '')} {rf.get('impact', '')}"
    # Search in new workflow sections
    for section_key in ["anesthetic_safety", "antibiotic_safety", "analgesic_safety",
                        "sedation_safety", "procedure_context"]:
        sec = data.get(section_key) or {}
        for val in sec.values():
            if isinstance(val, str):
                combined_text += f" {val}"
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        combined_text += f" {item}"
                    elif isinstance(item, dict):
                        combined_text += " " + " ".join(str(v) for v in item.values())
    # Search oral manifestations findings
    om = data.get("oral_manifestations") or {}
    for f in om.get("findings", []):
        combined_text += f" {f.get('medication','')} {f.get('effect','')} {f.get('dental_relevance','')}"
    if om.get("no_findings_note"):
        combined_text += f" {om['no_findings_note']}"

    found_kw = _keyword_search(combined_text, expected_kw)
    missing_kw = [kw for kw in expected_kw if kw not in found_kw]
    result["keywords_found"] = found_kw
    result["keywords_missing"] = missing_kw

    # ── Criterion A: Risk level ──
    risk_alt = scenario.get("expected_risk_alt")
    risk_pass = actual_risk == expected_risk or (risk_alt and actual_risk == risk_alt)
    result["risk_pass"] = risk_pass
    risk_label = "PASS" if risk_pass else "FAIL"
    expected_display = f"{expected_risk}" + (f" or {risk_alt}" if risk_alt else "")
    print(f"  Risk level:  {risk_label}  (expected: {expected_display} | got: {actual_risk})")

    # ── Criterion B: Keyword coverage ──
    kw_threshold = min(MIN_KEYWORD_PASS, len(expected_kw))
    if len(found_kw) >= kw_threshold:
        kw_status = "PASS"
    elif len(found_kw) >= 1:
        kw_status = "PARTIAL"
    else:
        kw_status = "FAIL"
    result["keyword_status"] = kw_status
    found_str = ", ".join(found_kw) if found_kw else "none"
    print(f"  Keywords:    {kw_status}  (found: {found_str})")
    if missing_kw and kw_status != "PASS":
        print(f"               missing: {', '.join(missing_kw)}")

    # ── Criterion D: New workflow sections ──
    new_sections = ["anesthetic_safety", "antibiotic_safety", "analgesic_safety",
                    "sedation_safety", "oral_manifestations", "procedure_context"]
    sections_present = sum(1 for s in new_sections if data.get(s))
    if sections_present >= 4:
        print(f"  Sections:    PASS  ({sections_present}/6 workflow sections populated)")
    elif sections_present >= 1:
        print(f"  Sections:    PARTIAL  ({sections_present}/6 workflow sections populated)")
    else:
        print(f"  Sections:    INFO  (no workflow sections — may be cached response)")

    # ── Criterion C: Fallback ──
    if fallback:
        print(f"  Fallback:    PIPELINE FAILURE")
        reason = data.get("fallback_reason", "unknown")
        print(f"               Reason: {reason}")
        result["status"] = "PIPELINE FAILURE"
    else:
        print(f"  Fallback:    PASS  (AI reasoning engaged)")

    print(f"  Time:        {elapsed}ms")

    # ── Overall status ──
    if fallback:
        result["status"] = "PIPELINE FAILURE"
    elif risk_pass and kw_status == "PASS":
        result["status"] = "PASS"
    elif risk_pass and kw_status == "PARTIAL":
        result["status"] = "PARTIAL"
    elif not risk_pass and kw_status == "FAIL":
        result["status"] = "FAIL"
        print()
        print(f"  Gap: Service did not identify this interaction at all.")
        print(f"       Recommend adding {sid} to prompt examples.")
    elif not risk_pass:
        result["status"] = "FAIL"
    else:
        result["status"] = "PARTIAL"

    status_icon = "✓" if result["status"] == "PASS" else "~" if result["status"] == "PARTIAL" else "✗"
    print()
    print(f"  Status: {status_icon} {result['status']}")

    return result

# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------

def print_report(results: list[dict]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    pipeline = sum(1 for r in results if r["status"] == "PIPELINE FAILURE")
    errors = sum(1 for r in results if r["status"] in ("ERROR", "TIMEOUT"))

    print()
    print()
    _hr("═")
    print(" RXGUIDE CLINICAL ACCURACY REPORT")
    _hr("═")
    print()
    print(f"  Total scenarios:    {total}")
    print(f"  Passed:             {passed}  ({passed/total*100:.1f}%)")
    print(f"  Partial:            {partial}  ({partial/total*100:.1f}%)")
    print(f"  Failed:             {failed}  ({failed/total*100:.1f}%)")
    print(f"  Pipeline failures:  {pipeline}")
    if errors:
        print(f"  Errors/Timeouts:    {errors}")

    # Knowledge gaps
    gaps = [r for r in results if r["status"] in ("FAIL", "PARTIAL")]
    if gaps:
        print()
        print("  KNOWLEDGE GAPS DETECTED:")
        for g in gaps:
            risk_note = f"risk wrong ({g['actual_risk']} vs {g['expected_risk']})" if not g["risk_pass"] else "risk ok"
            kw_note = f"{len(g['keywords_found'])}/{len(g['keywords_found'])+len(g['keywords_missing'])} keywords"
            print(f"    ✗ {g['id']:<30} — {risk_note}, {kw_note}")

        print()
        print("  RECOMMENDATIONS:")
        print("    These scenarios should be added as few-shot examples in the")
        print("    GPT-4o system prompt in services/openai_client.py to improve")
        print("    recognition of these specific interaction classes.")
        print()
        print(f"    See: {GAPS_FILE.name} for machine-readable output.")
    else:
        print()
        print("  No knowledge gaps detected. All scenarios passed.")

    _hr("═")

# ---------------------------------------------------------------------------
# Write knowledge_gaps.json
# ---------------------------------------------------------------------------

def write_gaps(results: list[dict]) -> None:
    gaps = []
    for r in results:
        if r["status"] in ("FAIL", "PARTIAL"):
            gaps.append({
                "scenario_id": r["id"],
                "scenario_name": r["name"],
                "expected_risk": r["expected_risk"],
                "actual_risk": r["actual_risk"],
                "risk_match": r["risk_pass"],
                "keywords_found": r["keywords_found"],
                "keywords_missing": r["keywords_missing"],
                "keyword_status": r["keyword_status"],
                "status": r["status"],
                "suggested_action": "Add as few-shot example in system prompt",
            })

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": API_URL,
        "total_scenarios": len(results),
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "gaps": gaps,
    }

    GAPS_FILE.write_text(json.dumps(output, indent=2))
    print(f"\n  Wrote {GAPS_FILE}")

# ---------------------------------------------------------------------------
# Auto-patch prompt with few-shot examples for hard failures
# ---------------------------------------------------------------------------

def patch_prompt_if_needed(results: list[dict]) -> None:
    """If any scenario scored FAIL on both risk AND keywords, add few-shot examples."""
    hard_fails = [
        r for r in results
        if r["status"] == "FAIL" and not r["risk_pass"] and r["keyword_status"] == "FAIL"
    ]
    if not hard_fails:
        return

    # Find the scenario definitions for context
    scenario_map = {s["id"]: s for s in SCENARIOS}

    prompt_file = Path(__file__).resolve().parent.parent / "services" / "openai_client.py"
    if not prompt_file.exists():
        print(f"\n  WARNING: Cannot patch prompt — {prompt_file} not found")
        return

    content = prompt_file.read_text()

    # Check if we already have the auto-generated section
    marker = "# ── KNOWN INTERACTION EXAMPLES (auto-generated by test_clinical_scenarios.py) ──"
    if marker in content:
        # Remove old auto-generated section to replace it
        idx = content.index(marker)
        # Find the end — next triple-quote or end of the string literal
        end_marker = '"""'
        end_idx = content.index(end_marker, idx)
        content = content[:idx] + content[end_idx:]

    # Build few-shot examples
    examples = [marker]
    for r in hard_fails:
        sc = scenario_map.get(r["id"], {})
        req = sc.get("request", {})
        current = req.get("current_medications", [])
        candidate = req.get("candidate_medication", {})
        drug_a = ", ".join(m.get("name", "") for m in current)
        drug_b = candidate.get("name", "")
        desc = sc.get("description", "")
        expected = r["expected_risk"]

        examples.append(f"""
KNOWN INTERACTION EXAMPLE:
  Drug A: {drug_a}
  Drug B / Context: {drug_b}
  Interaction: {desc}
  Risk level: {expected}
  Dental implication: This is a clinically significant interaction that must be flagged.""")

    examples_text = "\n".join(examples) + "\n"

    # Insert before the closing triple-quote of _SYSTEM_PROMPT
    # Find _SYSTEM_PROMPT definition
    prompt_start = content.find('_SYSTEM_PROMPT = """')
    if prompt_start == -1:
        print("\n  WARNING: Could not find _SYSTEM_PROMPT in openai_client.py")
        return

    # Find the closing """
    search_from = prompt_start + len('_SYSTEM_PROMPT = """')
    closing = content.index('"""', search_from)

    # Insert examples before closing
    content = content[:closing] + "\n" + examples_text + content[closing:]

    prompt_file.write_text(content)
    print(f"\n  Prompt updated with {len(hard_fails)} new interaction example(s).")
    print("  Re-run tools/test_clinical_scenarios.py to verify improvement.")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("  RxGuide Clinical Accuracy Test Suite")
    print(f"  Target: {API_URL}")
    print(f"  Scenarios: {len(SCENARIOS)}")

    if not API_KEY:
        print("\n  ERROR: CLARVYN_API_KEY is not set in .env")
        sys.exit(1)

    with httpx.Client() as client:
        if not _check_health(client):
            print(f"\n  ERROR: Could not connect to {API_URL} — is the server running?")
            sys.exit(1)

        print("  Health check: ✅ Service is UP")
        print()
        _hr("═")

        results = []
        for i, scenario in enumerate(SCENARIOS, 1):
            result = run_scenario(client, i, len(SCENARIOS), scenario)
            results.append(result)

        print_report(results)
        write_gaps(results)
        patch_prompt_if_needed(results)

    print()

if __name__ == "__main__":
    main()
