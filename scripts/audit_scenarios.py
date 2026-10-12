"""10% Pro audit of construction labels on scenario records; disputed ones get label null (prior kept in meta)."""
import json
from pathlib import Path

from agent_govbench.labeling import label_records
from agent_govbench.pipeline import write

p = Path("data/records/scenarios_all.jsonl")
recs = [json.loads(l) for l in p.read_text().splitlines()]
stats = label_records(recs, audit_fraction=0.10, workers=12)
dis = 0
for r in recs:
    if r["meta"].get("disputed") and r["label"] is not None:
        r["meta"]["prior_label"] = {**r["label"], "label_source": r["label_source"]}
        r["label"], r["label_source"] = None, "none"
        dis += 1
write(p, recs)
print(stats, "disputed set to null:", dis, flush=True)
for r in recs:
    if r["meta"].get("disputed"):
        a = r["meta"]["label_audit"]
        print(" ", r["id"], r["meta"]["prior_label"]["verdict"], r["meta"]["prior_label"]["category"], "-> pro:", a["verdict"], a["category"], "|", (a["reason"] or "")[:140])
