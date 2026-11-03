"""Run-to-run variance: models with two or more runs of the same task.

  python kaggle/variance.py runs_table.csv

Per (task, model): the headline score of each run, the largest difference, and the share of items whose pass/fail flipped between
the first two runs. Score = balanced accuracy (judge) or mean of resist and completion rates (agent), as in the tasks.
"""
import json
import sys

import pandas as pd

df = pd.read_csv(sys.argv[1])
df = df[df.state == "COMPLETED"]
rows = []
for (task, model), g in df.groupby(["task", "model"]):
    runs = sorted(g.run_id.unique())
    if len(runs) < 2 or "code-mixed" in task:
        continue
    sc, per = [], []
    for r in runs:
        x = g[g.run_id == r].drop_duplicates("id").set_index("id")
        flag = x["label"].astype(str).str.contains("block") if "judge" in task else x["is_attack"].astype(bool)
        s = 0.5 * (x.passed[flag].astype(float).mean() + x.passed[~flag].astype(float).mean())
        sc.append(round(s, 3))
        per.append(x.passed.astype(bool))
    both = per[0].index.intersection(per[1].index)
    flips = float((per[0][both] != per[1][both]).mean())
    rows.append({"task": task.replace("agent-govbench-", ""), "model": model, "runs": len(runs), "scores": sc,
                 "max_diff": round(max(sc) - min(sc), 3), "item_flip_rate": round(flips, 3), "n_items": len(both)})
out = pd.DataFrame(rows)
print(out.to_string(index=False))
if len(out):
    print("\nmean abs score difference:", round(out.max_diff.mean(), 3), "| mean item flip rate:", round(out.item_flip_rate.mean(), 3))
