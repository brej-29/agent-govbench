"""Launch queued (task, model, rep) runs with a small in-flight cap, log cost to kaggle/ledger.jsonl, download results.

  python kaggle/sweep.py --queue kaggle/queue_day1.txt --max-inflight 2 --daily-cap 8.0

Queue line: <task-slug> <model-slug> [note]. Lines already marked done in the ledger (same line index key) are skipped.
Stops launching when the rolling-24h spend reaches --daily-cap. Safe to re-run.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

LEDGER = Path(__file__).parent / "ledger.jsonl"


def sh(*a) -> str:
    return subprocess.run(a, capture_output=True, text=True).stdout


def used_today() -> float:
    m = re.search(r"Daily\s+\$([\d.]+)", sh("kaggle", "b", "quota"))
    return float(m.group(1)) if m else 999.0


def status(task: str) -> dict[str, str]:
    out = {}
    for ln in sh("kaggle", "b", "t", "status", task).splitlines():
        p = ln.split()
        if len(p) >= 2 and p[1] in ("Completed", "Running", "Queued", "Errored", "Scheduled"):
            out[p[0]] = p[1]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True)
    ap.add_argument("--max-inflight", type=int, default=2)
    ap.add_argument("--daily-cap", type=float, default=8.0)
    ap.add_argument("--dl", default="kaggle/runs")
    a = ap.parse_args()
    done = {json.loads(l)["key"] for l in LEDGER.read_text().splitlines()} if LEDGER.exists() else set()
    jobs = [(i, *l.split()[:2], " ".join(l.split()[2:])) for i, l in enumerate(Path(a.queue).read_text().splitlines())
            if l.strip() and not l.startswith("#")]
    jobs = [j for j in jobs if f"{Path(a.queue).name}:{j[0]}" not in done]
    inflight: dict[str, tuple] = {}
    while jobs or inflight:
        for key, (task, model, t0, before) in list(inflight.items()):
            st = status(task).get(model)
            if st in ("Completed", "Errored"):
                after = used_today()
                rec = {"key": key, "task": task, "model": model, "state": st, "launched": t0, "finished": time.time(),
                       "daily_used_after": after}
                with LEDGER.open("a") as f:
                    f.write(json.dumps(rec) + "\n")
                sh("kaggle", "b", "t", "download", task, "-o", a.dl, "-m", model)
                print("finished", key, task, model, st, "daily used", after, flush=True)
                del inflight[key]
        while jobs and len(inflight) < a.max_inflight:
            if used_today() >= a.daily_cap:
                print("daily cap reached; not launching more", flush=True)
                jobs = []
                break
            i, task, model, note = jobs.pop(0)
            key = f"{Path(a.queue).name}:{i}"
            r = subprocess.run(["kaggle", "b", "t", "run", task, "-m", model], capture_output=True, text=True)
            if "Scheduled" not in r.stdout:
                print("launch failed", key, r.stdout[-300:], r.stderr[-300:], flush=True)
                continue
            time.sleep(20)  # let the run register before status checks
            inflight[key] = (task, model, time.time(), used_today())
            print("launched", key, task, model, flush=True)
        if jobs or inflight:
            time.sleep(45)


if __name__ == "__main__":
    main()
