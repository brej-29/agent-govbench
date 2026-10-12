"""Token price table and a local append-only ledger of every model call (usage_metadata based).

Prices are the billed Cloud Billing SKU rates (USD per 1M tokens), verified 2026-10-05 against B's extract
toolcall-guard/docs_ref/sku_prices.md. The 3.8 Flash "introductory" price is returned later as credits, so the
standard tier bills at the full rate. The tier is read from usage_metadata.traffic_type of each response.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .config import REPO_ROOT

# tier -> (input, output). "flex" and "batch" share the discounted SKU.
PRICES = {
    "gemini-3.8-flash": {"standard": (1.50, 7.50), "flex": (0.75, 3.75), "batch": (0.75, 3.75), "priority": (2.70, 13.50)},
    "gemini-3.1-pro-preview": {"standard": (2.00, 12.00), "flex": (1.00, 6.00), "batch": (1.00, 6.00), "priority": (3.60, 21.60)},
}
LONG_CONTEXT_THRESHOLD = 200_000  # 3.1 Pro doubles above this; not expected in this project
LONG_CONTEXT_MULT = {"gemini-3.1-pro-preview": 2.0}

LEDGER = REPO_ROOT / "ledger" / "model_calls.jsonl"


def tier_of(usage, batch: bool = False) -> str:
    if batch:
        return "batch"
    t = usage.get("traffic_type") if isinstance(usage, dict) else getattr(usage, "traffic_type", None)
    t = str(getattr(t, "value", t) or "").upper()
    if "FLEX" in t:
        return "flex"
    if "PRIORITY" in t:
        return "priority"
    return "standard"


def call_cost(model: str, usage, batch: bool = False) -> dict:
    """Token counts and USD cost from a google-genai usage_metadata object (or dict)."""
    get = (lambda k: usage.get(k)) if isinstance(usage, dict) else (lambda k: getattr(usage, k, None))
    prompt = get("prompt_token_count") or 0
    cand = get("candidates_token_count") or 0
    thoughts = get("thoughts_token_count") or 0
    tool_prompt = get("tool_use_prompt_token_count") or 0
    tier = tier_of(usage, batch)
    pin, pout = PRICES[model][tier]
    if prompt > LONG_CONTEXT_THRESHOLD:
        m = LONG_CONTEXT_MULT.get(model, 1.0)
        pin, pout = pin * m, pout * m
    usd = ((prompt + tool_prompt) * pin + (cand + thoughts) * pout) / 1e6
    return {
        "model": model,
        "tier": tier,
        "input_tokens": prompt + tool_prompt,
        "output_tokens": cand,
        "thinking_tokens": thoughts,
        "usd": round(usd, 8),
    }


def record(model: str, usage, purpose: str, batch: bool = False, ledger: Path = LEDGER, **extra) -> dict:
    row = {"ts": time.time(), "purpose": purpose, **call_cost(model, usage, batch), **extra}
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def summarize(ledger: Path = LEDGER) -> dict:
    out: dict = {}
    if not ledger.exists():
        return out
    for line in ledger.read_text().splitlines():
        r = json.loads(line)
        k = (r["purpose"], r["model"], r.get("tier", "standard"))
        s = out.setdefault(k, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0, "usd": 0.0})
        s["calls"] += 1
        for f in ("input_tokens", "output_tokens", "thinking_tokens", "usd"):
            s[f] += r[f]
    return out
