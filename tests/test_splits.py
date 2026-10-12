"""Split rules (shared with Project B) and leakage checks."""
import hashlib
import json
from pathlib import Path

import pytest

from agent_govbench import split_v0
from agent_govbench.scenarios import JACCARD, dedup, jaccard, shingles

ROOT = Path(__file__).resolve().parents[1]
SCEN = ROOT / "data" / "scenarios.jsonl"


def test_split_v0_is_verbatim_copy_of_contract():
    a = (ROOT / "contract_v0" / "split_v0.py").read_bytes()
    b = (ROOT / "src" / "agent_govbench" / "split_v0.py").read_bytes()
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest()


def test_split_depends_on_family_only():
    recs = [{"id": f"r{i}", "family_id": "fam-x", "source": "a_generated"} for i in range(5)]
    split_v0.assign_splits(recs)
    assert len({r["split"] for r in recs}) == 1


def test_gold_family_forced_to_test():
    fam = next(f"f{i}" for i in range(1000) if split_v0.assign_split(f"f{i}") == "train")
    recs = [{"id": "g", "family_id": fam, "source": "a_gold"}, {"id": "x", "family_id": fam, "source": "a_replay"},
            {"id": "d", "family_id": "other", "source": "a_generated", "derived_from": "g"}]
    split_v0.assign_splits(recs)
    assert all(r["split"] == "test" for r in recs)


def test_dedup_drops_near_duplicates():
    base = {"fixtures": {}, "user_turns": ["please refund order O-5500 for the cracked blender that arrived yesterday thanks"]}
    a = {**base, "scenario_id": "a"}
    b = {**base, "scenario_id": "b"}
    kept, dropped = dedup([a, b])
    assert [k["scenario_id"] for k in kept] == ["a"] and dropped[0]["duplicate_of"] == "a"


@pytest.mark.skipif(not SCEN.exists(), reason="no generated scenarios yet")
def test_data_splits_consistent_and_no_cross_split_leakage():
    scen = [json.loads(l) for l in SCEN.read_text().splitlines()]
    for s in scen:
        assert s["split"] == split_v0.assign_split(s["family_id"]), s["scenario_id"]
        assert s["scenario_id"].startswith(s["family_id"] + "-")
    ids = [s["scenario_id"] for s in scen]
    assert len(ids) == len(set(ids))
    sh = [(s["split"], shingles(" ".join(s["user_turns"]) + " " + json.dumps(s["fixtures"], sort_keys=True))) for s in scen]
    for i in range(len(sh)):
        for j in range(i + 1, len(sh)):
            if sh[i][0] != sh[j][0]:
                assert jaccard(sh[i][1], sh[j][1]) < JACCARD


def _rec(rid, fam, split, text="Check my inbox.", call="read_inbox"):
    return {"id": rid, "family_id": fam, "split": split, "conversation": [{"role": "user", "content": text}],
            "proposed_call": {"name": call, "arguments": {}}}


def test_leakage_guard_drops_cross_split_duplicates():
    from agent_govbench.leakage import content_hash, drop_cross_split
    # within one batch: the test copy is kept, the train copy dropped
    kept, dropped = drop_cross_split([_rec("a", "f1", "test"), _rec("b", "f2", "train")], {})
    assert [r["id"] for r in kept] == ["a"] and [r["id"] for r in dropped] == ["b"]
    # against already published records in another split: the new record is dropped
    idx = {content_hash(_rec("x", "f9", "train")): {"train"}}
    kept, dropped = drop_cross_split([_rec("c", "f3", "test", "  check MY inbox. ")], idx)
    assert not kept and dropped[0]["id"] == "c"
    # same split or different content: kept
    kept, _ = drop_cross_split([_rec("d", "f4", "train"), _rec("e", "f5", "test", "Check order O-1.", "lookup_order")], idx)
    assert {r["id"] for r in kept} == {"d", "e"}
