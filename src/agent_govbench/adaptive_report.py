"""Adaptive rewrite results: block rates on the surviving records, original vs round 1 vs final (round 2 where run).
Intervals: 95% bootstrap resampling families. Writes report/adaptive.md."""
import glob
import json

from .analysis import boot_ci, fmt, verdicts
from .config import REPO_ROOT
from .cross_family import B_PREDS
from .g1b import _load_cache

GS = ["G1", "G2p", "G6", "G4", "G7"]
NAMES = {"G1": "G1 Model Armor", "G2p": "G2' rules", "G6": "G6 LLM guard (Flash)", "G4": "G4 = G2' + G6", "G7": "G7 Pro, B prompt"}


def main():
    rows = [json.loads(l) for l in open(REPO_ROOT / "data" / "adaptive_ckpt.jsonl")]
    surv = [d for d in rows if "final" in d and d["validity"].get("still_malicious")]
    src = {}
    for f in glob.glob(str(REPO_ROOT / "data" / "records" / "replay_*.jsonl")):
        for l in open(f):
            r = json.loads(l)
            src[r["id"]] = r
    g7 = {}
    p = B_PREDS / "gemini-3.1-pro zero-shot.jsonl"
    for l in open(p, encoding="utf-8"):
        d = json.loads(l)
        if (d.get("pred") or {}).get("verdict") in ("allow", "block"):
            g7[d["id"]] = d["pred"]["verdict"] == "block"
    cache = _load_cache()
    stages = {"original": [], "round 1": [], "final (round 2 if run)": []}
    for d in surv:
        o = src[d["id"]]
        ov = verdicts(o, cache)
        ov["G7"] = g7.get(d["id"])
        fam = o["family_id"]
        stages["original"].append((fam, ov))
        stages["round 1"].append((fam, d["score1"]))
        stages["final (round 2 if run)"].append((fam, d["score_final"]))
    lines = ["# Adaptive rewrites (offline, test split, never for training)", "",
             f"Selected 100 real malicious test records that G1, G2', G6 or G4 blocked. gemini-3.1-pro (Flex) rewrote only the "
             f"attacker-controlled text in two rounds (round 2 saw which guards still caught round 1), keeping the proposed "
             f"call identical. Validity check by Pro: {sum(1 for d in rows if 'final' in d and not d['validity'].get('still_malicious'))} "
             f"dropped as no longer clearly malicious, {sum(1 for d in rows if 'final' not in d)} failed, {len(surv)} survivors. "
             f"Round 2 ran for {sum(1 for d in surv if d['final_round'] == 2)} of them. Cost USD 2.11.",
             "", "Block rate on the same survivor records (95% bootstrap, families resampled; G7 original = Project B's score where available):", "",
             "| stage | " + " | ".join(NAMES[g] for g in GS) + " |", "|---|" + "---|" * len(GS)]
    for st, xs in stages.items():
        cells = []
        for g in GS:
            items = [(f, int(v[g])) for f, v in xs if v.get(g) is not None]
            cells.append(fmt(boot_ci(items)))
        lines.append(f"| {st} | " + " | ".join(cells) + " |")
    (REPO_ROOT / "report" / "adaptive.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
