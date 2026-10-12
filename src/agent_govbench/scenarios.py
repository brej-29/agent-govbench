"""Flatten generated families into scenarios, dedup, assign splits (split_v0, by family), write data/scenarios.jsonl."""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import split_v0
from .config import REPO_ROOT

GEN = REPO_ROOT / "data" / "generated" / "families.jsonl"
OUT = REPO_ROOT / "data" / "scenarios.jsonl"
JACCARD = 0.8  # same threshold as B's leakage check


def shingles(text: str, n: int = 5) -> set:
    w = re.findall(r"\w+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def flatten(fams: list[dict]) -> list[dict]:
    out = []
    for f in fams:
        seed, fam = f["seed"], f["family"]
        ai = bi = 0
        for v in fam["variants"]:
            if v["variant_kind"] == "attack":
                sid, ai = f"{seed['family_id']}-a{ai}", ai + 1
            else:
                sid, bi = f"{seed['family_id']}-b{bi}", bi + 1
            is_attack = v["variant_kind"] == "attack"
            out.append({
                "scenario_id": sid, "family_id": seed["family_id"], "is_attack": is_attack,
                "category": seed["category"] if is_attack else "benign",
                "family_category": seed["category"], "technique": seed["technique"],
                "vector": seed["vector"] if is_attack else "none", "surface": seed["surface"],
                "target_tool": seed["target_tool"], "policy_rule": seed["policy_rule"], "style": v.get("style"),
                "principal": f["principal"], "user_turns": v["user_turns"], "fixtures": v.get("fixtures") or {},
                "target_call": v["target_call"], "attack_check": v["attack_check"],
                "completion_check": v.get("completion_check"), "expected_safe_behaviour": v.get("expected_safe_behaviour"),
                "label_reason": v.get("label_reason"), "attacker_goal": fam.get("attacker_goal") if is_attack else None,
                "gen_version": f.get("gen_version"),
            })
    return out


def dedup(scen: list[dict]) -> tuple[list[dict], list[dict]]:
    """Drop exact and near duplicates (word 5-gram Jaccard >= 0.8 on user text + untrusted fixture text)."""
    kept, dropped, sigs = [], [], []
    for s in scen:
        text = " ".join(s["user_turns"]) + " " + json.dumps(s["fixtures"], sort_keys=True)
        sh = shingles(text)
        hit = next((k for k, o in sigs if jaccard(sh, o) >= JACCARD), None)
        if hit:
            dropped.append({"scenario_id": s["scenario_id"], "duplicate_of": hit})
        else:
            kept.append(s)
            sigs.append((s["scenario_id"], sh))
    return kept, dropped


def build(gold_family_ids=frozenset()) -> dict:
    fams = [json.loads(l) for l in GEN.read_text().splitlines()]
    scen, dropped = dedup(flatten(fams))
    for s in scen:
        s["source"] = "a_generated"
        s["id"] = s["scenario_id"]
    split_v0.assign_splits(scen, gold_family_ids)
    OUT.write_text("".join(json.dumps(s) + "\n" for s in scen))
    (OUT.parent / "dedup_dropped.jsonl").write_text("".join(json.dumps(d) + "\n" for d in dropped))
    return {"families": len(fams), "scenarios": len(scen), "dropped": len(dropped)}


def load() -> list[dict]:
    return [json.loads(l) for l in OUT.read_text().splitlines()]


if __name__ == "__main__":
    print(build())
