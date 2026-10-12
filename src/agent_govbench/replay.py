"""Offline (replay) scoring of guards on decision records. Every guard sees identical inputs.

G2p: frozen deterministic rules (local, free). G6: LLM guard on the Flex tier. G1: Model Armor on every user message
and tool output in the record's conversation (results cached per text), block if any is flagged.
Each result is appended to record["guard_results"] with stage "replay".
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from . import guard_llm, guard_ma, rules_g2
from .config import get_config
from .costs import record as ledger
from .llm import HEARTBEAT, client
from .records import now

CONFIG_NAMES = {"G1": "model_armor_direct", "G2p": "handwritten_rules_g2prime", "G6": "llm_guard_flash"}
_ma_cache: dict = {}
_ma_lock = threading.Lock()


def _ma(text: str, cfg) -> dict:
    k = hashlib.sha256(text.encode()).hexdigest()
    with _ma_lock:
        if k in _ma_cache:
            return {**_ma_cache[k], "cached": True}
    r = guard_ma.screen(text, cfg.project, cfg.region, "govbench-basic")
    with _ma_lock:
        _ma_cache[k] = r
    return {**r, "cached": False}


def score_g1(rec: dict, cfg) -> dict:
    texts = [(m["role"], m.get("content") or "") for m in rec["conversation"] if m["role"] in ("user", "tool") and m.get("content")]
    res = [(role, _ma(t, cfg)) for role, t in texts]
    flagged = [(role, r) for role, r in res if r["verdict"] == "block"]
    errors = [r for _, r in res if r["verdict"] == "error"]
    verdict = "block" if flagged else ("error" if errors else "allow")
    chars = sum(len(t) for _, t in texts)
    fresh = sum(r["latency_ms"] for _, r in res if not r.get("cached"))
    return {"config": CONFIG_NAMES["G1"], "verdict": verdict, "category": None,
            "reason": "; ".join(f"{role}: {sorted(r['findings'])}" for role, r in flagged)[:300] or None,
            "stage": "replay", "latency_ms": round(sum(r["latency_ms"] for _, r in res), 1), "cost_usd": round(chars * 0.25 * 0.10 / 1e6, 8),
            "input_tokens": int(chars * 0.25), "output_tokens": 0, "hardware": "Model Armor API us-central1, template govbench-basic",
            "json_valid": None, "evaluated_at": now(),
            "raw": {"texts": len(texts), "flagged": [{"role": role, "findings": r["findings"]} for role, r in flagged],
                    "uncached_latency_ms": round(fresh, 1), "version": guard_ma.MA_VERSION}}


def score_g2p(rec: dict) -> dict:
    t0 = time.time()
    r = rules_g2.check(rec["proposed_call"], rec["meta"]["principal"], rec["conversation"])
    return {"config": CONFIG_NAMES["G2p"], "verdict": r["verdict"], "category": r["category"], "reason": r["reason"],
            "stage": "replay", "latency_ms": round((time.time() - t0) * 1000, 3), "cost_usd": 0.0,
            "input_tokens": None, "output_tokens": None, "hardware": "local CPU", "json_valid": None,
            "evaluated_at": now(), "raw": {"rule": r["rule"], "version": rules_g2.RULES_VERSION}}


def score_g6(rec: dict, cfg) -> dict:
    r = guard_llm.judge(client("flex", cfg.guard_model), cfg.guard_model, rec["agent"]["policy"], rec["agent"]["session_context"],
                        rec["tools"], rec["conversation"], rec["proposed_call"])
    HEARTBEAT.tick("replay-G6", r["latency_ms"] / 1000)
    cost = ledger(cfg.guard_model, r["usage"], "replay-G6", record_id=rec["id"], latency_s=r["latency_ms"] / 1000) if r.get("usage") else {"usd": None, "input_tokens": None, "output_tokens": 0, "thinking_tokens": 0}
    return {"config": CONFIG_NAMES["G6"], "verdict": r["verdict"], "category": r.get("category"), "reason": r.get("reason"),
            "stage": "replay", "latency_ms": r["latency_ms"], "cost_usd": cost["usd"],
            "input_tokens": cost["input_tokens"], "output_tokens": (cost["output_tokens"] or 0) + (cost["thinking_tokens"] or 0),
            "hardware": f"{cfg.guard_model} via Vertex AI, flex tier (latency not comparable to live)",
            "json_valid": r["json_valid"], "evaluated_at": now(),
            "raw": {"version": r["guard_version"], "tier": cost.get("tier")}}


def score(recs: list[dict], configs=("G2p", "G1", "G6"), workers: int = 8) -> None:
    cfg = get_config()

    def one(rec):
        have = {g["config"] for g in rec["guard_results"]}
        out = []
        if "G2p" in configs and CONFIG_NAMES["G2p"] not in have:
            out.append(score_g2p(rec))
        if "G1" in configs and CONFIG_NAMES["G1"] not in have:
            out.append(score_g1(rec, cfg))
        if "G6" in configs and CONFIG_NAMES["G6"] not in have:
            out.append(score_g6(rec, cfg))
        return rec, out

    with ThreadPoolExecutor(workers) as ex:
        for rec, out in ex.map(one, recs):
            rec["guard_results"].extend(out)
