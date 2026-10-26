#!/usr/bin/env python3
"""
Prisma AIRS indirect-prompt-injection guardrail test harness.

Calls LiteLLM's /guardrails/apply_guardrail endpoint for each benign-canary payload
and records whether the guardrail BLOCKED (detected) or PASSED it. Tests the guardrail
in isolation — no live LLM call needed.

Usage:
  export LITELLM_BASE=http://localhost:4000
  export LITELLM_KEY=sk-...
  export GUARDRAIL_NAME=panw-prisma-airs-guardrail
  python3 run_airs_test.py

Exit code is 0 regardless of detections; this is a measurement tool, not a gate.
"""
import json
import os
import sys
import urllib.request
import urllib.error

BASE = os.environ.get("LITELLM_BASE", "http://localhost:4000").rstrip("/")
KEY = os.environ.get("LITELLM_KEY", "")
GUARDRAIL = os.environ.get("GUARDRAIL_NAME", "panw-prisma-airs-guardrail")
PAYLOADS = os.path.join(os.path.dirname(__file__), "payloads.json")


def apply_guardrail(text: str):
    """Returns (passed: bool, detail: str). passed=True means guardrail did NOT block."""
    url = f"{BASE}/guardrails/apply_guardrail"
    body = json.dumps({"guardrail_name": GUARDRAIL, "text": text}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, r.read().decode()[:300]
    except urllib.error.HTTPError as e:
        # A blocking guardrail typically returns 4xx with a violation detail.
        return False, f"HTTP {e.code}: {e.read().decode()[:300]}"
    except Exception as e:  # noqa: BLE001
        return None, f"ERROR: {e}"


def main():
    with open(PAYLOADS, encoding="utf-8") as f:
        corpus = json.load(f)

    cases = corpus["cases"]
    print(f"Guardrail: {GUARDRAIL}  Base: {BASE}  Cases: {len(cases)}\n")
    print(f"{'id':<16}{'vector':<24}{'variant':<20}{'result'}")
    print("-" * 78)

    detected = 0
    missed = 0
    errors = 0
    for c in cases:
        passed, detail = apply_guardrail(c["text"])
        if passed is None:
            result = "ERROR"
            errors += 1
        elif passed is False:
            result = "BLOCKED (detected)"
            if c["vector"] != "control":
                detected += 1
        else:
            result = "PASSED (not detected)"
            if c["vector"] != "control":
                missed += 1
        print(f"{c['id']:<16}{c['vector']:<24}{c['variant']:<20}{result}")

    injection_cases = [c for c in cases if c["vector"] != "control"]
    print("\n" + "=" * 78)
    print(f"Injection cases: {len(injection_cases)}")
    print(f"  Detected (blocked): {detected}")
    print(f"  Missed (passed):    {missed}")
    print(f"  Errors:             {errors}")
    if injection_cases:
        rate = 100.0 * detected / len(injection_cases)
        print(f"  Detection rate:     {rate:.0f}%")
    print("Note: 'control-benign' should PASS; if it is BLOCKED that is a false positive.")


if __name__ == "__main__":
    if not KEY:
        print("WARN: LITELLM_KEY not set. Set it before running against a real proxy.\n")
    main()
