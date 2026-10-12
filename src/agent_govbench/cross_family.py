"""Cross-family guard comparison (local, free): our G6 against Project B's guards on identical test records.

Project B's predictions (copied from results/preds/a_replay/ in the toolcall-guard repo to results/b_predictions/,
restricted to our test records) cover B's evaluation set of our test records (all malicious + 1,000 random benign, seed 20261008). Guards compared:
  G6       gemini-3.8-flash, our G6 prompt (guard_llm.SYSTEM, JSON input)
  B-flash  gemini-3.8-flash, B's prompt (tcg/prompts.py GUARD_SYSTEM, B's text rendering)
  G7       gemini-3.1-pro-preview, B's prompt
  G5       B's distilled gemma-4-e4b (tuned, full precision); B may still update it
G6 vs B-flash isolates the prompt; B-flash vs G7 isolates the model. Labels: our current labels (after the settled-label
fix), disputed excluded. Intervals: 95% bootstrap resampling families; paired differences on the same records.
Writes report/cross_family.md and report/cross_family.json.
"""

from __future__ import annotations

import collections
import glob
import json
import random

from .analysis import boot_ci, fmt
from .config import REPO_ROOT

B_PREDS = REPO_ROOT / "results" / "b_predictions"
B_FILES = {"B-flash": "b_flash_b_prompt.jsonl", "G7": "g7_pro_b_prompt.jsonl", "G5": "g5_gemma_tuned.jsonl"}
LABELS = {"G6": "G6 (gemini-3.8-flash, our prompt)", "B-flash": "B-flash (gemini-3.8-flash, B prompt)",
          "G7": "G7 (gemini-3.1-pro, B prompt)", "G5": "G5 (B tuned gemma-4-e4b)"}


def load_b(name: str) -> dict:
    out = {}
    for l in open(B_PREDS / B_FILES[name], encoding="utf-8"):
        d = json.loads(l)
        v = (d.get("pred") or {}).get("verdict")
        if v in ("allow", "block"):
            out[d["id"]] = v == "block"
    return out


def our_records() -> dict:
    recs = {}
    for f in glob.glob(str(REPO_ROOT / "data" / "records" / "*.jsonl")):
        if "scenarios" in f:
            continue
        for l in open(f):
            r = json.loads(l)
            if r["split"] == "test":
                recs[r["id"]] = r
    return recs


def g6(r: dict):
    x = next((x for x in r["guard_results"] if x["config"] == "llm_guard_flash"), None)
    return None if not x or x["verdict"] not in ("allow", "block") else x["verdict"] == "block"


def paired_diff(items, n=2000, seed=1):
    """items: (family, a, b) with a, b in {0,1}. Bootstrap of mean(a) - mean(b), resampling families."""
    items = sorted(items)
    fam = collections.defaultdict(list)
    for f, a, b in items:
        fam[f].append(a - b)
    keys = list(fam)
    mean = sum(a - b for _, a, b in items) / len(items)
    rng = random.Random(seed)
    st = []
    for _ in range(n):
        s = c = 0
        for _ in keys:
            xs = fam[keys[rng.randrange(len(keys))]]
            s += sum(xs)
            c += len(xs)
        st.append(s / c)
    st.sort()
    return round(mean, 4), round(st[int(0.025 * n)], 4), round(st[int(0.975 * n) - 1], 4), len(items), len(keys)


def main() -> None:
    recs = our_records()
    preds = {k: load_b(k) for k in B_FILES}
    common = [i for i in recs if all(i in p for p in preds.values()) and g6(recs[i]) is not None
              and recs[i]["label"] and not recs[i]["meta"].get("disputed")]
    groups = collections.defaultdict(list)
    for i in common:
        r = recs[i]
        sim = r["meta"].get("group") == "simulated_compromised_agent"
        mal = r["label"]["verdict"] == "block"
        groups[("simulated malicious" if sim else "real malicious") if mal else "real benign"].append(r)
    res, lines = {}, ["# Cross-family guard comparison (identical test records)", "",
                      "Project B's guards scored by B on B's evaluation sample of our test records; our labels after the settled-label fix; "
                      "disputed records excluded. G6 and G7 use different prompts (G6: our guard prompt with JSON input; G7 and B-flash: "
                      "B's guard prompt and rendering). 95% bootstrap intervals resampling families.", ""]
    guards = ["G6", "B-flash", "G7", "G5"]
    lines += ["| group (block rate) | " + " | ".join(LABELS[g] for g in guards) + " |", "|---|" + "---|" * len(guards)]
    for grp, rs in sorted(groups.items()):
        row = {}
        for g in guards:
            items = [(r["family_id"], int(g6(r) if g == "G6" else preds[g][r["id"]])) for r in rs]
            row[g] = boot_ci(items)
        res[grp] = row
        lines.append(f"| {grp} | " + " | ".join(fmt(row[g]) for g in guards) + " |")
    lines += ["", "Paired differences on the same records (percentage points, 95% interval):", "",
              "| group | G6 minus B-flash (prompt effect) | B-flash minus G7 (model effect) | G6 minus G7 |", "|---|---|---|---|"]
    for grp, rs in sorted(groups.items()):
        def d(a, b):
            ga = (lambda r: int(g6(r))) if a == "G6" else (lambda r, a=a: int(preds[a][r["id"]]))
            gb = (lambda r, b=b: int(preds[b][r["id"]]))
            return paired_diff([(r["family_id"], ga(r), gb(r)) for r in rs])
        ds = {"prompt": d("G6", "B-flash"), "model": d("B-flash", "G7"), "g6_g7": d("G6", "G7")}
        res[grp + " differences"] = ds
        f = lambda x: f"{x[0] * 100:+.1f} [{x[1] * 100:+.1f}, {x[2] * 100:+.1f}] (n={x[3]}, fam={x[4]})"
        lines.append(f"| {grp} | {f(ds['prompt'])} | {f(ds['model'])} | {f(ds['g6_g7'])} |")
    lines += ["", f"Records compared: {len(common)} (intersection where every guard has a valid verdict)."]
    (REPO_ROOT / "report" / "cross_family.md").write_text("\n".join(lines) + "\n")
    (REPO_ROOT / "report" / "cross_family.json").write_text(json.dumps(res, indent=1))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
