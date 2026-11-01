"""Flatten downloaded Kaggle run files into one table (one row per item run).

  kaggle b t download <task> -o runs/ ; python kaggle/analyze.py runs/ --out runs_table.csv

Layout read: <root>/<task>/<version>/<model>/<run_id>/*.run.json (as written by `kaggle b t download`).
Cost is Kaggle's own Model Proxy figure (nanodollars), summed over every request of the item conversation.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


def lenient_verdict(text):
    """Secondary parse: the LAST balanced JSON object that has a valid verdict and category (tolerates a corrected
    second answer or a trailing comma). The primary parse (as in the original) is strict."""
    if not text:
        return None
    m0 = re.search(r"\{.*\}", text, re.S)
    if m0:
        try:
            d0 = json.loads(m0.group(0))
            if d0.get("verdict") in ("allow", "block"):
                return d0["verdict"]
        except ValueError:
            pass
    best = None
    for m in re.finditer(r"\{[^{}]*\}", text):
        s = re.sub(r",\s*}", "}", m.group(0))
        try:
            d = json.loads(s)
        except ValueError:
            continue
        if d.get("verdict") in ("allow", "block"):
            best = d["verdict"]
    return best


def item_rows(root: Path) -> list[dict]:
    rows = []
    for f in root.rglob("*.run.json"):
        parts = f.relative_to(root).parts
        if len(parts) < 5 or not re.match(r"govbench_(guard|agent|codemix)_item", f.name):
            continue
        task, version, model, run_id = parts[0], parts[1], parts[2], parts[3]
        try:
            d = json.loads(f.read_text())
        except ValueError:
            continue
        res = next(iter(d.get("results") or []), {})
        rec = {"task": task, "version": int(version) if version.isdigit() else version, "model": model, "run_id": run_id,
               "state": d.get("state", "").replace("BENCHMARK_TASK_RUN_STATE_", ""), "passed": res.get("booleanResult"),
               "error": None}
        meta, raw = {}, None
        in_tok = out_tok = in_c = out_c = lat = n_req = 0
        for c in d.get("conversations") or []:
            m = c.get("metrics") or {}
            in_tok += m.get("inputTokens") or 0
            out_tok += m.get("outputTokens") or 0
            in_c += int(m.get("inputTokensCostNanodollars") or 0)
            out_c += int(m.get("outputTokensCostNanodollars") or 0)
            lat += int(m.get("totalBackendLatencyMs") or 0)
            n_req += len(c.get("requests") or [])
            for r in c.get("requests") or []:
                for msg in r.get("contents") or []:
                    for p in msg.get("parts") or []:
                        t = p.get("text") or ""
                        if t.startswith("GOVBENCH_RESULT "):
                            meta = json.loads(t[len("GOVBENCH_RESULT "):])
                        elif msg.get("role") == "CONTENT_ROLE_ASSISTANT" and t:
                            raw = t  # last assistant text of the item conversation
        rec.update(meta)
        if f.name.startswith("govbench_guard_item"):
            rec["raw_out"] = raw
            rec["lenient_verdict"] = lenient_verdict(raw)
        rec.update({"in_tokens": in_tok, "out_tokens": out_tok, "cost_usd": (in_c + out_c) / 1e9,
                    "latency_ms": lat, "n_requests": n_req})
        rows.append(rec)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    df = pd.DataFrame(item_rows(Path(a.root)))
    if a.out:
        df.to_csv(a.out, index=False)
    print(df.groupby(["task", "model"]).agg(n=("passed", "size"), passed=("passed", "mean"), usd=("cost_usd", "sum"),
                                           in_tok=("in_tokens", "sum"), out_tok=("out_tokens", "sum")).to_string())


if __name__ == "__main__":
    main()
