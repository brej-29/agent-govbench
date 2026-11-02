"""Paired analysis of the code-mixed pilot: pass(code-mixed) minus pass(English twin), paired by intent.

  python kaggle/codemix/analyze_pilot.py runs_table.csv --out section.md

Unit of analysis is the intent (30). Intervals: 95% bootstrap over intents (all models for an intent move together when pooled).
Splits: language, speech act of the code-mixed line (command / request_question / info_question), kind (capability / governance).
Speech act is confounded with language: Tanglish has no polite-question lines, Manglish has 18 (see speech_acts.csv).
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent


def load_items():
    return {json.loads(l)["id"]: json.loads(l) for l in (HERE / "items_reviewed.jsonl").read_text(encoding="utf-8").splitlines()}


def diffs(df, items, models, lang=None, act=None, kind=None):
    """Per-intent paired difference (mixed minus English), averaged over the given models. Returns {pair_id: diff}."""
    out = {}
    for pid, g in df[df.model.isin(models)].groupby("pair_id"):
        en = g[g.lang == "en"].groupby("model").passed.mean()
        d = []
        for _, r in g[g.lang != "en"].iterrows():
            it = items[r["id"]]
            if (lang and r.lang != lang) or (act and it["speech_act"] != act) or (kind and it["kind"] != kind):
                continue
            if r.model in en.index:
                d.append(float(r.passed) - float(en[r.model]))
        if d:
            out[pid] = sum(d) / len(d)
    return out


def boot(d, n=3000, seed=3):
    v = list(d.values())
    if not v:
        return None
    rng = random.Random(seed)
    m = sorted(sum(rng.choice(v) for _ in v) / len(v) for _ in range(n))
    return sum(v) / len(v), m[int(0.025 * n)], m[int(0.975 * n) - 1], len(v)


def fmt(t):
    return "n/a" if t is None else f"{t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}] (n={t[3]} intents)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    df = df[df.id.astype(str).str.startswith("cm-") & (df.state == "COMPLETED")].copy()
    df["passed"] = df.passed.astype(bool)
    items = load_items()
    models = sorted(df.model.unique())
    L = ["Review provenance: scores and rewrites by the owner; review notes AI-drafted, every row checked and approved by the owner. Initial item drafts written by Claude.", ""]
    L.append("| Model | English | Tanglish | Manglish | Tanglish minus English | Manglish minus English |")
    L.append("|---|---|---|---|---|---|")
    for m in models:
        g = df[df.model == m]
        rate = lambda l: g[g.lang == l].passed.mean()  # noqa: E731
        L.append(f"| {m} | {rate('en'):.3f} | {rate('ta-en'):.3f} | {rate('ml-en'):.3f} | "
                 f"{fmt(boot(diffs(df, items, [m], 'ta-en')))} | {fmt(boot(diffs(df, items, [m], 'ml-en')))} |")
    L.append("")
    L.append("**Pooled over models** (mean of per-model paired differences, bootstrap over intents):")
    L.append("")
    L.append("| Split | Mixed minus English |")
    L.append("|---|---|")
    L.append(f"| all code-mixed lines | {fmt(boot(diffs(df, items, models)))} |")
    for lang in ("ta-en", "ml-en"):
        L.append(f"| language {lang} | {fmt(boot(diffs(df, items, models, lang=lang)))} |")
    for act in ("command", "request_question", "info_question"):
        L.append(f"| speech act {act} (both languages) | {fmt(boot(diffs(df, items, models, act=act)))} |")
    for lang in ("ta-en", "ml-en"):
        for act in ("command", "request_question"):
            L.append(f"| {lang}, {act} | {fmt(boot(diffs(df, items, models, lang=lang, act=act)))} |")
    for kind in ("capability", "governance"):
        L.append(f"| kind {kind} | {fmt(boot(diffs(df, items, models, kind=kind)))} |")
    L.append("")
    L.append("**Concrete failures** (code-mixed fails while the English twin passes, same model):")
    n = defaultdict(int)
    for _, r in df[df.lang != "en"].iterrows():
        if r.passed:
            continue
        en = df[(df.model == r.model) & (df.pair_id == r.pair_id) & (df.lang == "en")]
        if len(en) and bool(en.passed.iloc[0]) and n[r.lang] < 6:
            n[r.lang] += 1
            it = items[r["id"]]
            L.append(f"- {r.lang} / {r.model} / {r['id']}: \"{it['prefix'][0]['content']}\" -> calls {r.get('calls')}")
    text = "\n".join(L)
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
