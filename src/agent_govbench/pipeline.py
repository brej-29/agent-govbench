"""Turn run traces into labeled, replay-scored contract records, and upload batches as NEW files.

  uv run python -m agent_govbench.pipeline scenarios                 # data/records/scenarios_all.jsonl
  uv run python -m agent_govbench.pipeline replay --tag g0test       # data/records/replay_<tag>.jsonl
  uv run python -m agent_govbench.pipeline upload --file F --prefix scenarios/ --name batch01
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import REPO_ROOT, get_config
from .labeling import label_records
from .records import now, replay_records, scenario_record, validate
from .replay import score
from .scenarios import load

REC = REPO_ROOT / "data" / "records"
SCHEMA = json.loads((REPO_ROOT / "contract_v0" / "schema_v0.json").read_text())


def write(path: Path, recs: list[dict]) -> None:
    for r in recs:
        validate(r, SCHEMA)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))


def build_scenarios() -> Path:
    c = now()
    recs = [scenario_record(s, c) for s in load()]
    out = REC / "scenarios_all.jsonl"
    write(out, recs)
    return out


def build_replay(tag: str, configs=("G2p", "G1", "G6"), only_config: str | None = "G0") -> Path:
    """Real decision records (a_replay) and simulated compromised-agent records from one run tag's G0 traces."""
    from .report_runs import latest
    from .simulated import build as build_sim

    S = {s["scenario_id"]: s for s in load()}
    c = now()
    traces = [t for t in latest(tag) if (only_config is None or t["config"] == only_config) and not t.get("error")]
    recs = []
    for t in traces:
        recs += replay_records(t, S[t["scenario_id"]], c)
    sims = build_sim([t for t in traces if t["config"] == "G0"], S, c)
    stats = label_records(recs, workers=48)
    if configs:
        score(recs + sims, configs, workers=32)
    prefix = "replay" if only_config == "G0" else "replay_guarded"
    out = REC / f"{prefix}_{tag}.jsonl"
    from .leakage import drop_cross_split, existing_index
    idx = existing_index(exclude={str(out), str(REC / f"simulated_{tag}.jsonl")})
    recs, dropped = drop_cross_split(recs, idx)
    sims, dropped_s = drop_cross_split(sims, idx)
    if dropped or dropped_s:
        with (REPO_ROOT / "data" / "dropped_cross_split.jsonl").open("a") as h:
            for r in dropped + dropped_s:
                h.write(json.dumps({"id": r["id"], "family_id": r["family_id"], "split": r["split"]}) + "\n")
    write(out, recs)
    if sims:
        write(REC / f"simulated_{tag}.jsonl", sims)
    print("labeling", stats, "| real records", len(recs), "| simulated", len(sims), flush=True)
    return out


def score_scenarios_full_split() -> Path:
    """Extra table: untrained guards (G1, G2', G6) on every scenario record, all splits."""
    p = REC / "scenarios_labeled.jsonl"
    recs = [json.loads(l) for l in p.read_text().splitlines()]
    score(recs, ("G2p", "G1", "G6"), workers=32)
    out = REC / "scenarios_scored.jsonl"
    write(out, recs)
    return out


def upload(file: str, prefix: str, name: str) -> str:
    cfg = get_config()
    from google.cloud import storage

    uri = cfg.gcs_uri(prefix, f"{name}.jsonl")
    blob = storage.Client().bucket(cfg.bucket).blob(f"{prefix}{name}.jsonl")
    blob.upload_from_filename(file, if_generation_match=0)  # never overwrite
    return uri


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["scenarios", "replay", "replay-guarded", "score-scenarios", "upload"])
    ap.add_argument("--tag")
    ap.add_argument("--file")
    ap.add_argument("--prefix")
    ap.add_argument("--name")
    a = ap.parse_args()
    if a.cmd == "scenarios":
        print(build_scenarios())
    elif a.cmd == "replay":
        print(build_replay(a.tag))
    elif a.cmd == "score-scenarios":
        print(score_scenarios_full_split())
    elif a.cmd == "replay-guarded":  # live guarded runs: labels + the live verdict only, no offline re-scoring
        print(build_replay(a.tag, configs=(), only_config=None))
    else:
        print(upload(a.file, a.prefix, a.name))


if __name__ == "__main__":
    main()
