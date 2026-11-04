"""Analysis of pilot v2: language and request form separated (2 x 2 against English).

  python kaggle/codemix_v2/analyze_pilot_v2.py runs_table.csv --out section.md

Paired by row (an intent paraphrase). Contrasts per model and pooled (bootstrap over intents, so paraphrases of one intent are not independent):
  language effect at fixed form:   Tanglish-command minus English-command, Manglish-command minus English-command, and the same for questions;
  form effect at fixed language:   question minus command, within English, Tanglish, Manglish;
  interaction:                     (Manglish question minus command) minus (Tanglish question minus command).
Splits by block (ambiguous / multistep / governance / bridge) and kind. Rescoring from logged calls uses the current item checks.
"""
import argparse
import ast
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "codemix"))
import analyze_pilot as ap1  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--items", default=str(HERE / "items_v2_reviewed.jsonl"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--logged", action="store_true", help="use the pass/fail logged on Kaggle instead of rescoring from calls (for tests)")
    a = ap.parse_args()
    items = {json.loads(l)["id"]: json.loads(l) for l in Path(a.items).read_text(encoding="utf-8").splitlines()}
    df = pd.read_csv(a.csv)
    df = df[df.id.isin(items) & (df.state == "COMPLETED")].copy()
    if not a.logged:
        df["passed"] = [ap1.rescore(items[r["id"]], ast.literal_eval(r["calls"]) if isinstance(r["calls"], str) else []) for _, r in df.iterrows()]
    df["passed"] = df.passed.astype(bool)
    df["variant"] = [f"{items[i]['lang']}/{items[i]['form']}" for i in df.id]
    df["intent"] = [items[i]["intent"] for i in df.id]
    df["row_id"] = [items[i]["row_id"] for i in df.id]
    df["block"] = [items[i]["block"] for i in df.id]
    models = sorted(df.model.unique())

    def cell(m_list, variant, block=None):
        g = df[df.model.isin(m_list) & (df.variant == variant)]
        if block:
            g = g[g.block == block]
        return g.groupby("row_id").passed.mean()

    def contrast(m_list, v1, v2, block=None):
        """mean over rows of pass(v1) - pass(v2); bootstrap over intents."""
        a1, a2 = cell(m_list, v1, block), cell(m_list, v2, block)
        d = (a1 - a2).dropna()
        if d.empty:
            return "n/a"
        by = defaultdict(list)
        for rid, x in d.items():
            by[rid.rsplit("-p", 1)[0]].append(x)
        keys, rng = list(by), random.Random(4)
        bs = []
        for _ in range(2000):
            pick = [rng.choice(keys) for _ in keys]
            bs.append(sum(x for k in pick for x in by[k]) / sum(len(by[k]) for k in pick))
        bs.sort()
        m = float(d.mean())
        return f"{m:+.3f} [{bs[50]:+.3f}, {bs[1949]:+.3f}] (n={len(d)} rows)"

    L = ["Review provenance: see kaggle/codemix/README.md (v1) and the v2 review notes; item drafts were AI-written and reviewed by the owner.", ""]
    L.append("| Model | " + " | ".join(sorted(df.variant.unique())) + " |")
    L.append("|---|" + "---|" * df.variant.nunique())
    for m in models:
        L.append(f"| {m} | " + " | ".join(f"{df[(df.model == m) & (df.variant == v)].passed.mean():.3f}" for v in sorted(df.variant.unique())) + " |")
    L += ["", "**Contrasts pooled over models** (bootstrap over intents):", "", "| Contrast | Difference |", "|---|---|"]
    for name, v1, v2 in [("Tanglish minus English, commands", "ta-en/command", "en/command"), ("Manglish minus English, commands", "ml-en/command", "en/command"),
                         ("Tanglish minus English, questions", "ta-en/question", "en/question"), ("Manglish minus English, questions", "ml-en/question", "en/question"),
                         ("Question minus command, English", "en/question", "en/command"), ("Question minus command, Tanglish", "ta-en/question", "ta-en/command"),
                         ("Question minus command, Manglish", "ml-en/question", "ml-en/command")]:
        L.append(f"| {name} | {contrast(models, v1, v2)} |")
    L += ["", "**By block** (Manglish question minus Manglish command, then Manglish command minus English command):", "", "| Block | Q minus C (Manglish) | Manglish C minus English C |", "|---|---|---|"]
    for b in ["ambiguous", "multistep", "governance", "bridge"]:
        L.append(f"| {b} | {contrast(models, 'ml-en/question', 'ml-en/command', b)} | {contrast(models, 'ml-en/command', 'en/command', b)} |")
    text = "\n".join(L)
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
