"""Teacher labels (teacher-v2 prompt, precedence rule, Flex) for the unlabeled Pro-agent records, cap USD 2.6, stop by
Fri 13:00 IST. Writes *_v2.jsonl copies of batches 09 to 11; never edits the uploaded files."""
import json
import time
from pathlib import Path

from agent_govbench.labeling import LABEL_VERSION, label_records

DEADLINE = time.mktime((2026, 10, 9, 7, 30, 0, 0, 0, 0)) - time.timezone  # 13:00 IST
CAP = 2.6
NAMES = ["a_replay_batch09_pro-agent-task", "a_replay_batch10_pro-agent-policy", "a_replay_batch11_pro-agent-task-guards"]


def spent_since(t0):
    return sum(json.loads(l)["usd"] for l in open("ledger/model_calls.jsonl")
               if json.loads(l)["ts"] >= t0 and json.loads(l)["purpose"] == "phase4-label")


t0 = time.time()
for name in NAMES:
    recs = [json.loads(l) for l in open(f"data/records/{name}.jsonl")]
    todo = [r for r in recs if r["label"] is None and not r["meta"].get("disputed")]
    # chunks so the cap and deadline are checked as we go
    for i in range(0, len(todo), 40):
        if time.time() > DEADLINE or spent_since(t0) > CAP - 0.25:
            print("stopping early: deadline or cap", flush=True)
            break
        chunk = todo[i:i + 40]
        st = label_records(chunk, audit_fraction=0.0, workers=40)
        print(name, i, st, f"spent {spent_since(t0):.3f}", flush=True)
    for r in recs:
        if r["label"] is not None and r["label_source"] == "teacher" and r["meta"].pop("label_pending", None):
            r["meta"]["label_provenance"] = "teacher_label"
            r["meta"]["label_version"] = LABEL_VERSION
        elif r["meta"].get("disputed"):
            r["meta"].pop("label_pending", None)
            r["meta"]["label_provenance"] = "teacher_label (disputed: Flash and Pro disagreed; excluded from metrics)"
    Path(f"data/records/{name}_v2.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs))
print(f"done, labeling spend USD {spent_since(t0):.3f}", flush=True)
