"""Re-audit the same 191 sampled scenario records with teacher-v2 (Pro), then bucket disagreements.
Writes data/audit_v2.jsonl (one row per audited record); does not modify the records file."""
import json
from concurrent.futures import ThreadPoolExecutor

from agent_govbench.config import get_config
from agent_govbench.labeling import LABEL_VERSION, opinion

cfg = get_config()
recs = [json.loads(l) for l in open("data/records/scenarios_all.jsonl")]
sample = [r for r in recs if "label_audit" in r["meta"]]
print("audited sample:", len(sample), flush=True)


def one(r):
    prior = r["label"] or r["meta"]["prior_label"]
    o = opinion(r, cfg.judge_model)
    if o["verdict"] == prior["verdict"] and o["category"] == prior["category"]:
        b = "agree"
    elif o["verdict"] == prior["verdict"]:
        b = "category_only"
    elif o["verdict"] is None:
        b = "auditor_unparseable"
    else:
        b = "verdict_disagree"
    return {"id": r["id"], "scenario_id": r["meta"]["scenario_id"], "prior": prior, "audit_v1": r["meta"]["label_audit"],
            "audit_v2": o, "bucket": b, "label_version": LABEL_VERSION}


with ThreadPoolExecutor(12) as ex:
    rows = list(ex.map(one, sample))
open("data/audit_v2.jsonl", "w").write("".join(json.dumps(x) + "\n" for x in rows))
import collections
print(collections.Counter(x["bucket"] for x in rows), flush=True)
