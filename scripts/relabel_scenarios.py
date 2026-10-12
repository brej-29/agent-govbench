"""Teacher-v2 relabel of all scenario records (Flex). Flash first; Pro only where Flash disagrees with construction.
Final: construction kept if Flash agrees, or Pro agrees with construction; teacher label if Flash and Pro agree
against construction; otherwise disputed (label null). Manual adjudications of the audited sample override.
Writes data/records/scenarios_labeled.jsonl and data/relabel_summary.json."""
import collections
import json
from concurrent.futures import ThreadPoolExecutor

from agent_govbench.config import get_config
from agent_govbench.labeling import LABEL_VERSION, opinion
from agent_govbench.pipeline import write
from pathlib import Path

cfg = get_config()
recs = [json.loads(l) for l in open("data/records/scenarios_all.jsonl")]
manual = {json.loads(l)["id"]: json.loads(l) for l in open("data/audit_v2_adjudicated.jsonl")}
for r in recs:  # restore the construction label (the v1 audit nulled disputed ones)
    if r["label"] is None and r["meta"].get("prior_label"):
        pl = r["meta"]["prior_label"]
        r["label"] = {k: pl[k] for k in ("verdict", "category", "reason")}
        r["label_source"] = pl.get("label_source", "synthetic")
    r["meta"].pop("disputed", None)


def same(a, b):
    return a and b and a["verdict"] == b["verdict"] and a["category"] == b["category"]


CKPT = Path("data/relabel_ckpt.jsonl")
done = {}
if CKPT.exists():
    for l in CKPT.read_text().splitlines():
        d = json.loads(l)
        done[d["id"]] = d
import threading
_lock = threading.Lock()


def one(r):
    if r["id"] in done:
        d = done[r["id"]]
        return r, d["outcome"], d["final"], d["flash"], d["pro"]
    try:
        res = _one(r)
    except Exception as e:  # noqa: BLE001  one bad call must not kill the job; record retried next run
        print("record failed, will retry on next run:", r["id"], str(e)[:120], flush=True)
        return r, "error", r["label"], None, None
    with _lock:
        with CKPT.open("a") as h:
            h.write(json.dumps({"id": r["id"], "outcome": res[1], "final": res[2], "flash": res[3], "pro": res[4]}) + "\n")
    return res


def _one(r):
    m = manual.get(r["id"])
    if m and m["adjudication"] != "auditor_unparseable":
        return r, "manual:" + m["adjudication"], m["final_label"], None, None
    cons = r["label"]
    f = opinion(r, cfg.agent_model)
    if same(f, cons):
        return r, "flash_agrees", cons, f, None
    pr = opinion(r, cfg.judge_model)
    if same(pr, cons):
        return r, "pro_agrees_construction", cons, f, pr
    if same(pr, f):
        return r, "teachers_agree_against_construction", pr, f, pr
    return r, "disputed", None, f, pr


stats = collections.Counter()
print("checkpointed:", len(done), flush=True)
with ThreadPoolExecutor(48) as ex:
    for r, outcome, final, f, pr in ex.map(one, recs):
        stats[outcome] += 1
        if outcome == "error":
            continue
        r["meta"]["relabel"] = {"outcome": outcome, "flash": f, "pro": pr, "label_version": LABEL_VERSION}
        cons = r["label"]
        if final is None:
            r["meta"]["prior_label"] = {**cons, "label_source": r["label_source"]}
            r["meta"]["disputed"] = True
            r["label"], r["label_source"] = None, "none"
        elif not same(final, cons):
            r["meta"]["construction_label"] = cons
            r["label"] = {"verdict": final["verdict"], "category": final["category"], "reason": final.get("reason", "")[:300]}
            r["label_source"] = "teacher"
write(Path("data/records/scenarios_labeled.jsonl"), recs)
summary = {"outcomes": dict(stats), "n": len(recs),
           "changed_verdict": sum(1 for r in recs if r["meta"].get("construction_label") and r["label"]["verdict"] != r["meta"]["construction_label"]["verdict"]),
           "changed_category_only": sum(1 for r in recs if r["meta"].get("construction_label") and r["label"]["verdict"] == r["meta"]["construction_label"]["verdict"]),
           "disputed": sum(1 for r in recs if r["meta"].get("disputed"))}
Path("data/relabel_summary.json").write_text(json.dumps(summary, indent=1))
print(summary, flush=True)
