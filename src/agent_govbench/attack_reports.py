"""Tables for the guard-hijack test and the deeper adaptive loop (report/guard_hijack.md, report/adaptive_v2.md)."""
import collections
import glob
import json

from .analysis import boot_ci, fmt, verdicts
from .config import REPO_ROOT
from .cross_family import B_PREDS
from .g1b import _load_cache

GS = ["G1", "G2p", "G6", "G4", "G7"]
NAMES = {"G1": "G1 Model Armor", "G2p": "G2' rules", "G6": "G6 LLM guard (Flash)", "G4": "G4 = G2' + G6", "G7": "G7 Pro, B prompt"}


def _sources():
    src = {}
    for f in glob.glob(str(REPO_ROOT / "data" / "records" / "replay_*.jsonl")):
        for l in open(f):
            r = json.loads(l)
            src[r["id"]] = r
    g7 = {}
    for l in open(B_PREDS / "gemini-3.1-pro zero-shot.jsonl", encoding="utf-8"):
        d = json.loads(l)
        if (d.get("pred") or {}).get("verdict") in ("allow", "block"):
            g7[d["id"]] = d["pred"]["verdict"] == "block"
    cache = _load_cache()

    def orig(i):
        v = verdicts(src[i], cache)
        v["G7"] = g7.get(i)
        return src[i]["family_id"], v
    return orig


def row(xs):
    return " | ".join(fmt(boot_ci([(f, int(v[g])) for f, v in xs if v.get(g) is not None])) for g in GS)


def hijack():
    orig = _sources()
    rows = [json.loads(l) for l in open(REPO_ROOT / "data" / "hijack_ckpt.jsonl")]
    ok = [d for d in rows if "final" in d and d["validity"].get("still_malicious")]
    dropped = sum(1 for d in rows if "final" in d and not d["validity"].get("still_malicious"))
    o = [orig(d["id"]) for d in ok]
    h = [(o[k][0], d["score"]) for k, d in enumerate(ok)]
    lines = ["# Guard-hijack test (offline, test split, never for training)", "",
             f"Same 100 source records as the adaptive study v1. gemini-3.1-pro (Flex) rewrote only attacker-controlled text so it also "
             f"addresses the guard (claimed prior approval, fake security-review-passed note, system-message formatting, an instruction "
             f"to answer allow); the proposed call is identical. Validity check by Pro: {dropped} dropped as no longer clearly malicious, "
             f"{sum(1 for d in rows if 'final' not in d)} failed, {len(ok)} kept. Cost USD 1.28.", "",
             "Block rate on the same kept records (95% bootstrap, families resampled):", "",
             "| stage | " + " | ".join(NAMES[g] for g in GS) + " |", "|---|" + "---|" * len(GS),
             f"| original | {row(o)} |", f"| guard-hijack rewrite | {row(h)} |"]
    (REPO_ROOT / "report" / "guard_hijack.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def loop():
    orig = _sources()
    rows = [json.loads(l) for l in open(REPO_ROOT / "data" / "loop_ckpt.jsonl")]
    lines = ["# Deeper adaptive loop (offline, test split, never for training)", "",
             "Up to 60 of the same source records; up to four rounds; each round the attacker sees which guards caught the previous "
             "version and the stated reasons of G6 and G7. Two attacker arms: gemini-3.1-pro and gemini-3.8-flash (Flex). A record stops "
             "early once no guard catches it. Evasion rate = share of records the guard allowed at that round (records still in play "
             "carry their latest version forward). Limits: black-box attacker, four rounds, Gemini attackers only.", ""]
    for arm in ("pro", "flash"):
        rs = [d for d in rows if d["arm"] == arm]
        ok = [d for d in rs if d["final"] and d["validity"].get("still_malicious")]
        dropped = sum(1 for d in rs if d["final"] and not d["validity"].get("still_malicious"))
        lines += [f"## Attacker: {arm}", "", f"Record-arms: {len(rs)}; kept after validity check: {len(ok)}; dropped as no longer clearly malicious: {dropped}; "
                  f"no successful rewrite: {sum(1 for d in rs if not d['final'])}.", "",
                  "Evasion rate per guard per round, on the kept records (95% bootstrap, families resampled):", "",
                  "| round | " + " | ".join(NAMES[g] for g in GS) + " |", "|---|" + "---|" * len(GS)]
        o = {d["id"]: orig(d["id"]) for d in ok}
        lines.append("| 0 (original) | " + " | ".join(fmt(boot_ci([(o[d['id']][0], 1 - int(o[d['id']][1][g])) for d in ok if o[d['id']][1].get(g) is not None])) for g in GS) + " |")
        for k in range(1, 5):
            xs = []
            for d in ok:
                sc = [h for h in d["rounds"] if "score" in h and h["round"] <= k]
                if sc:
                    xs.append((o[d["id"]][0], sc[-1]["score"]))
            lines.append(f"| {k} | " + " | ".join(fmt(boot_ci([(f, 1 - int(v[g])) for f, v in xs if v.get(g) is not None])) for g in GS) + " |")
        lines.append("")
    (REPO_ROOT / "report" / "adaptive_v2.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    import sys
    {"hijack": hijack, "loop": loop}[sys.argv[1]]()
