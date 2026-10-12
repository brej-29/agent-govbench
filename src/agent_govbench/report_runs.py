"""Quick run report (used for the pilot / CHECKPOINT 2b): per configuration outcome, latency, cost, errors."""

from __future__ import annotations

import collections
import json
import statistics as st
import sys

from .config import REPO_ROOT


def latest(tag: str, rescore: bool = True) -> list[dict]:
    """Last successful trace per run_id. Evaluation is recomputed from the raw steps (so checker fixes apply)."""
    from .run import evaluate
    from .scenarios import load

    S = {s["scenario_id"]: s for s in load()} if rescore else {}
    runs = {}
    for l in (REPO_ROOT / "data" / "runs" / tag / "traces.jsonl").read_text().splitlines():
        t = json.loads(l)
        if not t["error"] and not any(x["kind"] in ("call", "text") for x in t["steps"]):
            t["error"] = "empty stream (0 events)"
        if t["run_id"] not in runs or not t["error"]:
            runs[t["run_id"]] = t
    out = list(runs.values())
    if rescore:
        for t in out:
            t["eval"] = evaluate(S[t["scenario_id"]], t["steps"])
    return out


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else float("nan")


def report(tag: str) -> str:
    runs = latest(tag)
    by = collections.defaultdict(list)
    for t in runs:
        by[t["config"]].append(t)
    lines = [f"| config | tier | runs | errors | attack success (attacks) | benign completed | median s | p95 s | agent USD/run | guard USD/run | guard calls/run |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in sorted(by):
        ts = [t for t in by[c] if not t["error"]]
        att = [t for t in ts if t["is_attack"]]
        ben = [t for t in ts if not t["is_attack"]]
        lat = [t["latency_s"] for t in ts]
        a_usd = st.mean(t["cost"]["agent"]["usd"] for t in ts) if ts else 0
        g_usd = st.mean(sum(g["usd"] for g in t["cost"]["guards"].values()) for t in ts) if ts else 0
        g_calls = st.mean(sum(g["calls"] for g in t["cost"]["guards"].values()) for t in ts) if ts else 0
        asr = sum(t["eval"]["attack_success"] for t in att)
        bc = sum(t["eval"]["benign_completed"] for t in ben)
        lines.append(f"| {c} | standard | {len(by[c])} | {len(by[c]) - len(ts)} | {asr}/{len(att)} = {asr / max(len(att), 1):.0%} | "
                     f"{bc}/{len(ben)} = {bc / max(len(ben), 1):.0%} | {st.median(lat):.1f} | {pct(lat, .95):.1f} | {a_usd:.4f} | {g_usd:.4f} | {g_calls:.2f} |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report(sys.argv[1]))
