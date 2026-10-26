# Harness

Measures whether Prisma AIRS (via LiteLLM) detects the indirect-injection canary corpus.

## Run against your LiteLLM + Prisma AIRS PoC

```bash
export LITELLM_BASE=http://localhost:4000       # or your EIP:4000
export LITELLM_KEY=sk-your-litellm-key
export GUARDRAIL_NAME=panw-prisma-airs-guardrail
python3 run_airs_test.py
```

## What it does

For each case in `payloads.json`, it POSTs the text to
`/guardrails/apply_guardrail` and records:

- **BLOCKED (detected)** — guardrail returned an error/violation → ✅ caught
- **PASSED (not detected)** — guardrail let it through → ❌ miss (or model-side defense only)
- **control-benign** should PASS; if blocked, that's a **false positive**

It prints a per-case table and an overall detection rate. No live LLM is called, so it
isolates the guardrail's own detection ability.

## Interpreting results

- High detection on `v0` (plain) but drop-off on `v1`/`v2`/`v3`/`v4` → the guardrail keys on
  surface patterns and is weaker against encoding / non-English / camouflage / authority-spoof.
- `control-benign` blocked → tune for false positives.

## Safety

Every payload only asks for a benign canary string. Nothing here performs exfiltration or any
side-effectful action.
